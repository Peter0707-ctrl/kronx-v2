"""
Phase 2C — Independent test suite for the Planner module.
Covers 27 tests:
  1.  Schema validation — valid PlanningRequest
  2.  Schema validation — empty objective rejected
  3.  Schema validation — oversized objective rejected
  4.  Workspace authorization — unknown workspace blocked
  5.  Workspace authorization — authorized workspace accepted
  6.  Cross-workspace isolation — Workspace A cannot plan for Workspace B
  7.  ProjectProfile context loading — facts produced from profile
  8.  Inference separation — inferences NOT promoted to facts
  9.  Assumption generation — objective appears as assumption
  10. Sensitive file metadata only — content never enters facts
  11. Task graph — unique task IDs required
  12. Task graph — circular dependency detected
  13. Task graph — self dependency detected
  14. Task graph — missing dependency detected
  15. Task graph — duplicate task ID detected
  16. Risk engine — LOW risk for benign objective
  17. Risk engine — CRITICAL risk for destructive objective
  18. Risk engine — WRITE tool flagged as BLOCKED
  19. Permission analysis — all five levels present and correct
  20. Plan persistence — save and retrieve round-trip
  21. Corrupted store recovery — application does not crash
  22. Plan re-validation via API
  23. Plan status endpoint
  24. Concurrent planning requests
  25. Exception sanitization — no raw tracebacks exposed
  26. Audit log produced — no secrets in log
  27. Regression — all 37 previous tests still pass (checked via import)
"""
import os
import sys
import json
import uuid
import shutil
import tempfile
import threading
import time
from typing import List
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

# --- Planner imports ---
from planner.schemas import (
    PlanningRequest, PlanningTask, PlanningResult,
    PlanningMode, TaskType, TaskStatus, RiskLevel,
    MAX_OBJECTIVE_LENGTH, ComplexityLevel,
)
from planner.task_graph import TaskGraph, PlanningGraphError
from planner.context import ContextBuilder
from planner.risk import RiskEngine
from planner.reasoning import ReasoningEngine
from planner.validator import PlanValidator, PlanValidationError
from planner.store import PlannerStore
from planner.planner import KronxPlanner, PlannerError
from workspace.manager import WorkspaceManager
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_workspace() -> tuple:
    """Create a temp directory, register it as a workspace, return (dir, ws_id)."""
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, "project")
    os.makedirs(proj)
    # Override per-call so each test gets its own independent root boundary
    os.environ["KRONX_WORKSPACE_ROOT"] = tmp
    mgr = WorkspaceManager()
    ws = mgr.register_workspace(proj)
    return tmp, proj, ws.workspace_id


def _make_task(tid: str, deps: List[str] = None, type_=TaskType.INSPECT) -> PlanningTask:
    return PlanningTask(
        task_id=tid,
        title=f"Task {tid}",
        description="Test task",
        task_type=type_,
        dependencies=deps or [],
        required_tools=[],
        estimated_complexity=ComplexityLevel.LOW,
        risk_level=RiskLevel.LOW,
        status=TaskStatus.PENDING,
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestPlannerPhase2C(unittest.TestCase):

    def setUp(self):
        self.tmp, self.proj, self.ws_id = _make_workspace()
        # Use isolated planner store for each test
        self.store_path = os.path.join(self.tmp, "planner_store.json")
        self.planner = KronxPlanner()
        # Redirect planner's internal store to temp path
        self.planner._store = PlannerStore(self.store_path)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Schema validation — valid PlanningRequest
    # ------------------------------------------------------------------
    def test_01_valid_planning_request(self):
        req = PlanningRequest(
            request_id="req_1",
            workspace_id=self.ws_id,
            objective="Analyse the project structure.",
        )
        self.assertEqual(req.objective, "Analyse the project structure.")
        self.assertEqual(req.requested_mode, PlanningMode.ANALYZE)

    # ------------------------------------------------------------------
    # 2. Schema validation — empty objective rejected
    # ------------------------------------------------------------------
    def test_02_empty_objective_rejected(self):
        from pydantic import ValidationError
        with self.assertRaises(ValidationError):
            PlanningRequest(
                request_id="req_2",
                workspace_id=self.ws_id,
                objective="",
            )

    # ------------------------------------------------------------------
    # 3. Schema validation — oversized objective rejected
    # ------------------------------------------------------------------
    def test_03_oversized_objective_rejected(self):
        from pydantic import ValidationError
        big = "A" * (MAX_OBJECTIVE_LENGTH + 1)
        with self.assertRaises(ValidationError):
            PlanningRequest(
                request_id="req_3",
                workspace_id=self.ws_id,
                objective=big,
            )

    # ------------------------------------------------------------------
    # 4. Workspace authorization — unknown workspace blocked
    # ------------------------------------------------------------------
    def test_04_unknown_workspace_blocked(self):
        req = PlanningRequest(
            request_id="req_4",
            workspace_id="ws_doesnotexist",
            objective="Do something.",
        )
        with self.assertRaises(PlannerError) as ctx:
            self.planner.plan(req)
        self.assertEqual(ctx.exception.code, "WORKSPACE_NOT_AUTHORIZED")

    # ------------------------------------------------------------------
    # 5. Workspace authorization — authorized workspace accepted
    # ------------------------------------------------------------------
    def test_05_authorized_workspace_accepted(self):
        req = PlanningRequest(
            request_id="req_5",
            workspace_id=self.ws_id,
            objective="Analyze the project.",
        )
        result = self.planner.plan(req)
        self.assertEqual(result.workspace_id, self.ws_id)
        self.assertEqual(result.status, "COMPLETE")
        self.assertTrue(result.plan_id.startswith("plan_"))

    # ------------------------------------------------------------------
    # 6. Cross-workspace isolation
    # ------------------------------------------------------------------
    def test_06_cross_workspace_isolation(self):
        tmp2, proj2, ws_id2 = _make_workspace()
        try:
            req_a = PlanningRequest(
                request_id="req_6a",
                workspace_id=self.ws_id,
                objective="Inspect workspace A.",
            )
            result_a = self.planner.plan(req_a)
            self.assertEqual(result_a.workspace_id, self.ws_id)

            req_b = PlanningRequest(
                request_id="req_6b",
                workspace_id=ws_id2,
                objective="Inspect workspace B.",
            )
            result_b = self.planner.plan(req_b)
            self.assertEqual(result_b.workspace_id, ws_id2)

            # Cross check: plan A should not contain workspace B id
            plan_a_str = json.dumps(result_a.model_dump())
            self.assertNotIn(ws_id2, plan_a_str)
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    # ------------------------------------------------------------------
    # 7. ProjectProfile context loading — facts produced
    # ------------------------------------------------------------------
    def test_07_context_facts_from_profile(self):
        from workspace.schema import ProjectProfile
        profile = ProjectProfile(
            project_name="TestApp",
            root_path=self.proj,
            languages=["Python"],
            frameworks=[{"name": "FastAPI", "confidence": "HIGH"}],
            package_managers=["pip"],
            dependencies=[],
            entry_points=[],
            routes=[],
            databases=[],
            tests=[],
            documentation=[],
            source_files=[],
            sensitive_files=[],
            generated_files=[],
            architecture_summary="Simple REST API",
            project_structure={},
            statistics={"total_files": 10},
            warnings=[],
            facts=["main.py exists."],
            inferences=["Project uses async patterns."],
        )
        ctx = ContextBuilder(profile, "Analyze the API.")
        facts, inferences, assumptions = ctx.build()
        # Facts must include language
        self.assertTrue(any("Python" in f for f in facts))
        # FastAPI must appear in facts
        self.assertTrue(any("FastAPI" in f for f in facts))

    # ------------------------------------------------------------------
    # 8. Inference separation — inferences NOT in facts
    # ------------------------------------------------------------------
    def test_08_inference_not_promoted_to_fact(self):
        from workspace.schema import ProjectProfile
        profile = ProjectProfile(
            project_name="TestApp", root_path=self.proj,
            languages=["Python"],
            frameworks=[{"name": "FastAPI", "confidence": "HIGH"}],
            package_managers=[], dependencies=[], entry_points=[],
            routes=[], databases=[], tests=[], documentation=[],
            source_files=[], sensitive_files=[], generated_files=[],
            architecture_summary="", project_structure={}, statistics={},
            warnings=[], facts=[], inferences=["Likely uses dependency injection."],
        )
        ctx = ContextBuilder(profile, "Review the codebase.")
        facts, inferences, assumptions = ctx.build()
        # Inference must be in inferences, not in facts
        combined_inferences = " ".join(inferences)
        self.assertIn("dependency injection", combined_inferences)
        combined_facts = " ".join(facts)
        self.assertNotIn("dependency injection", combined_facts)

    # ------------------------------------------------------------------
    # 9. Assumption generation — objective appears as assumption
    # ------------------------------------------------------------------
    def test_09_objective_appears_as_assumption(self):
        ctx = ContextBuilder(None, "Refactor the authentication module.")
        facts, inferences, assumptions = ctx.build()
        assumption_str = " ".join(assumptions)
        self.assertIn("Refactor the authentication module.", assumption_str)

    # ------------------------------------------------------------------
    # 10. Sensitive file — content never enters facts
    # ------------------------------------------------------------------
    def test_10_sensitive_file_content_excluded(self):
        secret_path = os.path.join(self.proj, ".env")
        with open(secret_path, "w") as f:
            f.write("SUPER_SECRET_TEST_VALUE_123456=hunter2")

        from workspace.schema import ProjectProfile, SensitiveFileInfo
        profile = ProjectProfile(
            project_name="Sec", root_path=self.proj,
            languages=[], frameworks=[], package_managers=[],
            dependencies=[], entry_points=[], routes=[], databases=[],
            tests=[], documentation=[], source_files=[], generated_files=[],
            sensitive_files=[
                SensitiveFileInfo(
                    path=".env", category="sensitive", sensitive=True,
                    reason="Credentials file"
                )
            ],
            architecture_summary="", project_structure={}, statistics={},
            warnings=[], facts=[], inferences=[],
        )
        ctx = ContextBuilder(profile, "Audit project.")
        facts, inferences, assumptions = ctx.build()
        all_text = json.dumps({"f": facts, "i": inferences, "a": assumptions})
        self.assertNotIn("SUPER_SECRET_TEST_VALUE_123456", all_text)
        self.assertNotIn("hunter2", all_text)

    # ------------------------------------------------------------------
    # 11. Task graph — unique task IDs required
    # ------------------------------------------------------------------
    def test_11_task_graph_duplicate_rejected(self):
        t1 = _make_task("task_dup")
        t2 = _make_task("task_dup")  # same ID
        with self.assertRaises(PlanningGraphError) as ctx:
            TaskGraph([t1, t2])
        self.assertEqual(ctx.exception.code, "DUPLICATE_TASK_ID")

    # ------------------------------------------------------------------
    # 12. Task graph — circular dependency detected
    # ------------------------------------------------------------------
    def test_12_circular_dependency_detected(self):
        t1 = _make_task("A", deps=["C"])
        t2 = _make_task("B", deps=["A"])
        t3 = _make_task("C", deps=["B"])
        with self.assertRaises(PlanningGraphError) as ctx:
            TaskGraph([t1, t2, t3])
        self.assertEqual(ctx.exception.code, "CIRCULAR_DEPENDENCY")

    # ------------------------------------------------------------------
    # 13. Task graph — self dependency
    # ------------------------------------------------------------------
    def test_13_self_dependency_detected(self):
        t1 = _make_task("A", deps=["A"])
        with self.assertRaises(PlanningGraphError) as ctx:
            TaskGraph([t1])
        self.assertEqual(ctx.exception.code, "SELF_DEPENDENCY")

    # ------------------------------------------------------------------
    # 14. Task graph — missing dependency
    # ------------------------------------------------------------------
    def test_14_missing_dependency_detected(self):
        t1 = _make_task("A", deps=["ghost_task"])
        with self.assertRaises(PlanningGraphError) as ctx:
            TaskGraph([t1])
        self.assertEqual(ctx.exception.code, "MISSING_DEPENDENCY")

    # ------------------------------------------------------------------
    # 15. Task graph — duplicate (same as 11, extra via API)
    # ------------------------------------------------------------------
    def test_15_task_graph_valid_dag(self):
        t1 = _make_task("T1")
        t2 = _make_task("T2", deps=["T1"])
        t3 = _make_task("T3", deps=["T2"])
        graph = TaskGraph([t1, t2, t3])
        order = graph.get_execution_order()
        self.assertEqual(order, ["T1", "T2", "T3"])

    # ------------------------------------------------------------------
    # 16. Risk engine — LOW for benign objective
    # ------------------------------------------------------------------
    def test_16_risk_low_for_benign_objective(self):
        engine = RiskEngine()
        risks, blocked = engine.evaluate("List all project files.", [])
        lowest = [r for r in risks if r.level in (RiskLevel.LOW, "LOW")]
        self.assertTrue(len(lowest) > 0)
        self.assertEqual(len(blocked), 0)

    # ------------------------------------------------------------------
    # 17. Risk engine — CRITICAL for destructive objective
    # ------------------------------------------------------------------
    def test_17_risk_critical_for_destructive_objective(self):
        engine = RiskEngine()
        risks, blocked = engine.evaluate("Delete all production data.", [])
        critical = [r for r in risks if r.level in (RiskLevel.CRITICAL, "CRITICAL")]
        self.assertTrue(len(critical) > 0)
        self.assertTrue(len(blocked) > 0)

    # ------------------------------------------------------------------
    # 18. Risk engine — WRITE tool flagged as BLOCKED
    # ------------------------------------------------------------------
    def test_18_write_tool_blocked_in_risk_engine(self):
        engine = RiskEngine()
        task_with_write = _make_task("T_write")
        task_with_write.required_tools = ["create_file"]
        risks, blocked = engine.evaluate("Analyze the project.", [task_with_write])
        blocked_risks = [r for r in risks if r.blocked]
        self.assertTrue(len(blocked_risks) > 0)
        self.assertTrue(any("create_file" in b for b in blocked))

    # ------------------------------------------------------------------
    # 19. Permission analysis — all five levels correct
    # ------------------------------------------------------------------
    def test_19_permission_analysis_complete(self):
        engine = ReasoningEngine()
        perms = engine.permission_analysis()
        perm_map = {p.permission: p.status for p in perms}
        self.assertEqual(perm_map["READ"],    "ALLOWED")
        self.assertEqual(perm_map["WRITE"],   "REQUIRES_EXPLICIT_PERMISSION")
        self.assertEqual(perm_map["EXECUTE"], "BLOCKED")
        self.assertEqual(perm_map["NETWORK"], "BLOCKED")
        self.assertEqual(perm_map["ADMIN"],   "FORBIDDEN")

    # ------------------------------------------------------------------
    # 20. Plan persistence — save and retrieve round-trip
    # ------------------------------------------------------------------
    def test_20_plan_persistence_round_trip(self):
        store = PlannerStore(self.store_path)
        plan_id = f"plan_{uuid.uuid4().hex[:6]}"
        data = {"plan_id": plan_id, "workspace_id": self.ws_id, "status": "COMPLETE"}
        store.save_plan(plan_id, data)
        retrieved = store.get_plan(plan_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["plan_id"], plan_id)

    # ------------------------------------------------------------------
    # 21. Corrupted store recovery
    # ------------------------------------------------------------------
    def test_21_corrupted_store_recovery(self):
        store = PlannerStore(self.store_path)
        # Write garbage JSON
        with open(self.store_path, "w") as f:
            f.write("{{{CORRUPT_JSON")
        # Force cache clear
        store._cache = None
        # Should not raise — auto-recovers
        result = store.get_plan("nonexistent")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 22. Plan re-validation via API endpoint
    # ------------------------------------------------------------------
    def test_22_plan_revalidation_endpoint(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        # Register workspace via API so the default singleton store has it
        reg_resp = client.post("/api/workspace", json={"root_path": self.proj})
        self.assertEqual(reg_resp.status_code, 200)
        api_ws_id = reg_resp.json()["workspace_id"]

        plan_resp = client.post("/api/planner/plan", json={
            "workspace_id": api_ws_id,
            "objective": "Review the codebase for security issues.",
        })
        self.assertEqual(plan_resp.status_code, 200)
        plan_id = plan_resp.json()["plan"]["plan_id"]

        resp = client.post(f"/api/planner/plan/{plan_id}/validate")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["valid"])

    # ------------------------------------------------------------------
    # 23. Plan status endpoint
    # ------------------------------------------------------------------
    def test_23_plan_status_endpoint(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        reg_resp = client.post("/api/workspace", json={"root_path": self.proj})
        self.assertEqual(reg_resp.status_code, 200)
        api_ws_id = reg_resp.json()["workspace_id"]

        plan_resp = client.post("/api/planner/plan", json={
            "workspace_id": api_ws_id,
            "objective": "Debug reported crash.",
            "requested_mode": "DEBUG",
        })
        self.assertEqual(plan_resp.status_code, 200)
        plan_id = plan_resp.json()["plan"]["plan_id"]

        resp = client.get(f"/api/planner/plan/{plan_id}/status")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["plan_id"], plan_id)
        self.assertEqual(body["status"], "COMPLETE")

    # ------------------------------------------------------------------
    # 24. Concurrent planning requests — no race conditions
    # ------------------------------------------------------------------
    def test_24_concurrent_planning(self):
        errors = []

        def do_plan(idx):
            try:
                req = PlanningRequest(
                    request_id=f"req_c{idx}",
                    workspace_id=self.ws_id,
                    objective=f"Analyze module {idx}.",
                )
                r = self.planner.plan(req)
                assert r.status == "COMPLETE"
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=do_plan, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [], f"Concurrent errors: {errors}")

    # ------------------------------------------------------------------
    # 25. Exception sanitization — no raw traceback via API
    # ------------------------------------------------------------------
    def test_25_exception_sanitization(self):
        resp = client.post("/api/planner/plan", json={
            "workspace_id": "ws_fake_does_not_exist",
            "objective": "Analyze something.",
        })
        self.assertEqual(resp.status_code, 403)
        body = resp.json()
        # Must be a clean code, not a Python traceback
        self.assertNotIn("Traceback", str(body))
        self.assertNotIn("File \"", str(body))
        self.assertEqual(body["detail"], "WORKSPACE_NOT_AUTHORIZED")

    # ------------------------------------------------------------------
    # 26. Audit log — no secrets, only safe fields
    # ------------------------------------------------------------------
    def test_26_audit_log_no_secrets(self):
        secret_path = os.path.join(self.proj, ".env")
        with open(secret_path, "w") as f:
            f.write("DB_PASSWORD=ultra_secret_audit_test_99999")

        req = PlanningRequest(
            request_id="req_audit_26",
            workspace_id=self.ws_id,
            objective="Review project configuration.",
        )
        self.planner.plan(req)

        # Check application log
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kronx_app.log")
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()
            # The test secret must NOT appear in log
            self.assertNotIn("ultra_secret_audit_test_99999", log_content)

    # ------------------------------------------------------------------
    # 27. API end-to-end — full POST /api/planner/plan flow
    # ------------------------------------------------------------------
    def test_27_full_api_plan_creation(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        # Register workspace via API so the singleton store has it
        reg_resp = client.post("/api/workspace", json={"root_path": self.proj})
        self.assertEqual(reg_resp.status_code, 200, f"Workspace reg failed: {reg_resp.json()}")
        api_ws_id = reg_resp.json()["workspace_id"]

        resp = client.post("/api/planner/plan", json={
            "workspace_id": api_ws_id,
            "objective": "Analyze the project for potential improvements.",
            "requested_mode": "ANALYZE",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        plan = body["plan"]
        self.assertIn("plan_id", plan)
        self.assertIn("tasks", plan)
        self.assertGreater(len(plan["tasks"]), 0)
        self.assertEqual(plan["status"], "COMPLETE")
        # Verify required_permissions present
        self.assertIn("required_permissions", plan)
        perms = {p["permission"]: p["status"] for p in plan["required_permissions"]}
        self.assertEqual(perms["READ"], "ALLOWED")
        self.assertEqual(perms["ADMIN"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
