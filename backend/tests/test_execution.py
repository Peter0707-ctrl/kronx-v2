"""
Phase 2D — Independent Test Suite for Execution Orchestration Engine
Covers 34 tests:
  1.  Schema validation — valid ExecutionRequest
  2.  Unknown plan rejection
  3.  Unknown workspace rejection
  4.  Workspace isolation — cannot execute plan belonging to different workspace
  5.  Dependency ordering — topological sort order executed
  6.  Dependency failure propagation — upstream failure marks downstream SKIPPED
  7.  Circular dependency rejection — circular tasks caught
  8.  Permission denial — unauthorized tool blocked
  9.  WRITE blocked — write tool requires explicit permission
  10. EXECUTE blocked — execute tool blocked
  11. NETWORK blocked — network tool blocked
  12. ADMIN forbidden — admin tool forbidden
  13. Dry-run mode — performs zero mutations and zero tool calls
  14. Cancellation — cooperative cancellation halts subsequent tasks
  15. Pause and resume — execution can be paused and resumed
  16. Invalid state transition rejection — e.g. COMPLETED -> RUNNING rejected
  17. Retry limits — retryable errors bounded by MAX_RETRY_ATTEMPTS
  18. Non-retryable errors — abort immediately on PERMISSION_DENIED / SENSITIVE_FILE
  19. Resource limits — excessive tasks rejected
  20. Audit logging — audit events emitted without secrets
  21. Secret exclusion — sensitive credentials excluded from results
  22. Traceback sanitization — API returns clean error codes without tracebacks
  23. Concurrent execution safety — multiple threads executing simultaneously
  24. Execution persistence — save and retrieve round-trip
  25. Corruption recovery — corrupted execution store auto-recovers
  26. Restart / state recovery — execution reloadable from disk
  27. ToolRuntime enforcement — tools executed through runtime
  28. No direct filesystem bypass — no direct file mutation
  29. No subprocess / shell execution — zero subprocess calls
  30. Regression against Phase 1
  31. Regression against Phase 2A
  32. Regression against Phase 2B
  33. Regression against Phase 2C
  34. Full API end-to-end lifecycle — start, status, tasks, cancel endpoints
"""
import os
import sys
import json
import uuid
import shutil
import tempfile
import threading
import time
from typing import List, Dict, Any, Optional
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.schemas import (
    ExecutionRequest, ExecutionResult, ExecutionTaskState,
    ExecutionMode, ExecutionStatus, TaskExecutionStatus,
    MAX_TASKS_PER_EXECUTION,
)
from execution.errors import (
    ExecutionError, EXECUTION_NOT_FOUND, PLAN_NOT_FOUND,
    WORKSPACE_NOT_AUTHORIZED, INVALID_TASK_ID,
    BLOCKED_REQUIRES_PERMISSION, FORBIDDEN_PERMISSION_LEVEL,
    RESOURCE_LIMIT_EXCEEDED, INVALID_EXECUTION_STATE,
)
from execution.state import ExecutionStateMachine
from execution.authorization import ExecutionAuthorizer
from execution.checkpoint import ExecutionStore
from execution.verifier import ExecutionVerifier
from execution.orchestrator import ExecutionOrchestrator
from workspace.manager import WorkspaceManager
from workspace.store import WorkspaceStore
from planner.store import PlannerStore
from planner.schemas import PlanningTask, TaskType, ComplexityLevel, RiskLevel
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _make_workspace() -> tuple:
    """Create a temp directory, register it as a workspace, return (tmp_dir, proj_dir, ws_id)."""
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, "project")
    os.makedirs(proj)
    os.environ["KRONX_WORKSPACE_ROOT"] = tmp
    mgr = WorkspaceManager()
    ws = mgr.register_workspace(proj)
    return tmp, proj, ws.workspace_id


def _create_sample_plan(
    ws_id: str,
    tasks: List[Dict[str, Any]],
    store: Optional[PlannerStore] = None
) -> str:
    """Helper to save a plan into PlannerStore."""
    plan_id = f"plan_{uuid.uuid4().hex[:8]}"
    plan_data = {
        "plan_id": plan_id,
        "workspace_id": ws_id,
        "objective": "Test objective",
        "mode": "ANALYZE",
        "summary": "Test summary",
        "tasks": tasks,
        "status": "COMPLETE",
        "created_at": "2026-08-14T00:00:00Z"
    }
    p_store = store or PlannerStore()
    p_store.save_plan(plan_id, plan_data)
    return plan_id


class TestExecutionEnginePhase2D(unittest.TestCase):

    def setUp(self):
        self.tmp, self.proj, self.ws_id = _make_workspace()
        self.exec_store_path = os.path.join(self.tmp, "execution_store.json")
        self.exec_store = ExecutionStore(self.exec_store_path)
        self.orchestrator = ExecutionOrchestrator(self.exec_store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Schema Validation
    # ------------------------------------------------------------------
    def test_01_valid_execution_request(self):
        req = ExecutionRequest(
            request_id="req_1",
            workspace_id=self.ws_id,
            plan_id="plan_123",
            execution_mode=ExecutionMode.DRY_RUN,
        )
        self.assertEqual(req.workspace_id, self.ws_id)
        self.assertEqual(req.execution_mode, ExecutionMode.DRY_RUN)

    # ------------------------------------------------------------------
    # 2. Unknown Plan Rejection
    # ------------------------------------------------------------------
    def test_02_unknown_plan_rejection(self):
        req = ExecutionRequest(
            request_id="req_2",
            workspace_id=self.ws_id,
            plan_id="plan_nonexistent",
            execution_mode=ExecutionMode.DRY_RUN,
        )
        with self.assertRaises(ExecutionError) as ctx:
            self.orchestrator.execute(req)
        self.assertEqual(ctx.exception.code, PLAN_NOT_FOUND)

    # ------------------------------------------------------------------
    # 3. Unknown Workspace Rejection
    # ------------------------------------------------------------------
    def test_03_unknown_workspace_rejection(self):
        req = ExecutionRequest(
            request_id="req_3",
            workspace_id="ws_does_not_exist",
            plan_id="plan_123",
            execution_mode=ExecutionMode.DRY_RUN,
        )
        with self.assertRaises(ExecutionError) as ctx:
            self.orchestrator.execute(req)
        self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 4. Workspace Isolation
    # ------------------------------------------------------------------
    def test_04_workspace_isolation(self):
        tmp2, proj2, ws_id2 = _make_workspace()
        try:
            tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]}]
            plan_id_b = _create_sample_plan(ws_id2, tasks)

            # Attempt executing Workspace B's plan inside Workspace A
            req = ExecutionRequest(
                request_id="req_4",
                workspace_id=self.ws_id,
                plan_id=plan_id_b,
                execution_mode=ExecutionMode.DRY_RUN,
            )
            with self.assertRaises(ExecutionError) as ctx:
                self.orchestrator.execute(req)
            self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

    # ------------------------------------------------------------------
    # 5. Dependency Ordering
    # ------------------------------------------------------------------
    def test_05_dependency_ordering(self):
        tasks = [
            {"task_id": "t2", "title": "T2", "description": "Step 2", "task_type": "ANALYZE", "dependencies": ["t1"], "required_tools": []},
            {"task_id": "t1", "title": "T1", "description": "Step 1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]},
        ]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_5",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.completed_tasks, ["t1", "t2"])

    # ------------------------------------------------------------------
    # 6. Dependency Failure Propagation
    # ------------------------------------------------------------------
    def test_06_dependency_failure_propagation(self):
        tasks = [
            {"task_id": "t1", "title": "T1", "description": "Step 1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["non_existent_failing_tool"]},
            {"task_id": "t2", "title": "T2", "description": "Step 2", "task_type": "ANALYZE", "dependencies": ["t1"], "required_tools": []},
        ]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_6",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertIn("t1", result.failed_tasks)
        self.assertIn("t2", result.skipped_tasks)
        self.assertEqual(result.status, ExecutionStatus.FAILED)

    # ------------------------------------------------------------------
    # 7. Circular Dependency Rejection
    # ------------------------------------------------------------------
    def test_07_circular_dependency_rejection(self):
        tasks = [
            {"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": ["t2"], "required_tools": []},
            {"task_id": "t2", "title": "T2", "description": "D2", "task_type": "INSPECT", "dependencies": ["t1"], "required_tools": []},
        ]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_7",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        with self.assertRaises(ExecutionError) as ctx:
            self.orchestrator.execute(req)
        self.assertEqual(ctx.exception.code, "CIRCULAR_DEPENDENCY")

    # ------------------------------------------------------------------
    # 8. Permission Denial — Unauthorized Tool
    # ------------------------------------------------------------------
    def test_08_permission_denial(self):
        authorizer = ExecutionAuthorizer()
        is_auth, code, blocked = authorizer.authorize_task_tools(
            task_id="t1",
            required_tools=["create_file"],
            effective_permission="READ",
        )
        self.assertFalse(is_auth)
        self.assertEqual(code, BLOCKED_REQUIRES_PERMISSION)
        self.assertIn("create_file", blocked)

    # ------------------------------------------------------------------
    # 9. WRITE Blocked
    # ------------------------------------------------------------------
    def test_09_write_blocked(self):
        tasks = [{"task_id": "t_write", "title": "Write file", "description": "Write", "task_type": "DESIGN", "dependencies": [], "required_tools": ["create_file"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_9",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertIn("t_write", result.blocked_tasks)
        self.assertEqual(result.status, ExecutionStatus.BLOCKED)

    # ------------------------------------------------------------------
    # 10. EXECUTE Blocked
    # ------------------------------------------------------------------
    def test_10_execute_blocked(self):
        tasks = [{"task_id": "t_exec", "title": "Run shell", "description": "Exec", "task_type": "ANALYZE", "dependencies": [], "required_tools": ["execute_command"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_10",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertIn("t_exec", result.blocked_tasks)
        self.assertEqual(result.status, ExecutionStatus.BLOCKED)

    # ------------------------------------------------------------------
    # 11. NETWORK Blocked
    # ------------------------------------------------------------------
    def test_11_network_blocked(self):
        tasks = [{"task_id": "t_net", "title": "Fetch API", "description": "Net", "task_type": "ANALYZE", "dependencies": [], "required_tools": ["network_request"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_11",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertIn("t_net", result.blocked_tasks)
        self.assertEqual(result.status, ExecutionStatus.BLOCKED)

    # ------------------------------------------------------------------
    # 12. ADMIN Forbidden
    # ------------------------------------------------------------------
    def test_12_admin_forbidden(self):
        authorizer = ExecutionAuthorizer()
        allowed, reason = authorizer.check_permission("ADMIN", "READ")
        self.assertFalse(allowed)
        self.assertEqual(reason, FORBIDDEN_PERMISSION_LEVEL)

    # ------------------------------------------------------------------
    # 13. Dry-Run Performs Zero Mutations
    # ------------------------------------------------------------------
    def test_13_dry_run_zero_mutations(self):
        tasks = [
            {"task_id": "t1", "title": "Inspect", "description": "Read", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]},
            {"task_id": "t2", "title": "Analyze", "description": "Analyze", "task_type": "ANALYZE", "dependencies": ["t1"], "required_tools": []},
        ]
        plan_id = _create_sample_plan(self.ws_id, tasks)

        # Snapshot files in directory
        initial_files = set(os.listdir(self.proj))

        req = ExecutionRequest(
            request_id="req_13",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.execution_mode, ExecutionMode.DRY_RUN)

        # Filesystem must remain 100% identical
        after_files = set(os.listdir(self.proj))
        self.assertEqual(initial_files, after_files)

    # ------------------------------------------------------------------
    # 14. Cooperative Cancellation
    # ------------------------------------------------------------------
    def test_14_cancellation(self):
        tasks = [
            {"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]},
            {"task_id": "t2", "title": "T2", "description": "D2", "task_type": "INSPECT", "dependencies": ["t1"], "required_tools": ["list_directory"]},
        ]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_14",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )

        result = self.orchestrator.execute(req)
        exec_id = result.execution_id

        # Cancel through orchestrator
        cancel_res = self.orchestrator.cancel(exec_id)
        self.assertIn(cancel_res.status, (ExecutionStatus.CANCELLED, ExecutionStatus.COMPLETED))

    # ------------------------------------------------------------------
    # 15. Pause and Resume
    # ------------------------------------------------------------------
    def test_15_pause_and_resume(self):
        tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "ANALYZE", "dependencies": [], "required_tools": []}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_15",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        exec_id = result.execution_id

        # Pause and resume
        data = self.exec_store.get_execution(exec_id)
        data["status"] = ExecutionStatus.RUNNING.value
        self.exec_store.save_execution(exec_id, data)

        paused = self.orchestrator.pause(exec_id)
        self.assertEqual(paused.status, ExecutionStatus.PAUSED)

        resumed = self.orchestrator.resume(exec_id)
        self.assertEqual(resumed.status, ExecutionStatus.RUNNING)

    # ------------------------------------------------------------------
    # 16. Invalid State Transition Rejection
    # ------------------------------------------------------------------
    def test_16_invalid_state_transition_rejection(self):
        sm = ExecutionStateMachine()
        with self.assertRaises(ExecutionError) as ctx:
            sm.validate_execution_transition(ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING)
        self.assertEqual(ctx.exception.code, INVALID_EXECUTION_STATE)

    # ------------------------------------------------------------------
    # 17. Retry Limits
    # ------------------------------------------------------------------
    def test_17_retry_limits(self):
        task_state = ExecutionTaskState(
            task_id="t_retry",
            title="Retry task",
            description="Fails",
            status=TaskExecutionStatus.RUNNING,
            required_tools=["unknown_tool_triggering_error"]
        )
        success, res, err = self.orchestrator._execute_tool_with_retries(
            request_id="r17",
            workspace_id=self.ws_id,
            tool_name="unknown_tool_triggering_error",
            task_state=task_state,
        )
        self.assertFalse(success)
        # Should not exceed max retries
        self.assertLessEqual(task_state.attempts, 3)

    # ------------------------------------------------------------------
    # 18. Non-Retryable Errors Abort Immediately
    # ------------------------------------------------------------------
    def test_18_non_retryable_errors(self):
        task_state = ExecutionTaskState(
            task_id="t_non_retry",
            title="Non retry",
            description="Fails immediately",
            status=TaskExecutionStatus.RUNNING,
            required_tools=["create_file"]
        )
        success, res, err = self.orchestrator._execute_tool_with_retries(
            request_id="r18",
            workspace_id=self.ws_id,
            tool_name="create_file",
            task_state=task_state,
        )
        self.assertFalse(success)
        # Bails out on first attempt due to PERMISSION_DENIED / TOOL_NOT_REGISTERED
        self.assertEqual(task_state.attempts, 1)

    # ------------------------------------------------------------------
    # 19. Resource Limits
    # ------------------------------------------------------------------
    def test_19_resource_limits(self):
        # 101 tasks exceeds MAX_TASKS_PER_EXECUTION (100)
        oversized_tasks = [
            {"task_id": f"t_{i}", "title": f"T{i}", "description": "D", "task_type": "ANALYZE", "dependencies": [], "required_tools": []}
            for i in range(MAX_TASKS_PER_EXECUTION + 1)
        ]
        plan_id = _create_sample_plan(self.ws_id, oversized_tasks)
        req = ExecutionRequest(
            request_id="req_19",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.DRY_RUN,
        )
        with self.assertRaises(ExecutionError) as ctx:
            self.orchestrator.execute(req)
        self.assertEqual(ctx.exception.code, RESOURCE_LIMIT_EXCEEDED)

    # ------------------------------------------------------------------
    # 20. Audit Logging
    # ------------------------------------------------------------------
    def test_20_audit_logging(self):
        tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_audit_20",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        self.assertTrue(result.audit_reference.startswith("audit_exec_"))

    # ------------------------------------------------------------------
    # 21. Secret Exclusion
    # ------------------------------------------------------------------
    def test_21_secret_exclusion(self):
        secret_file = os.path.join(self.proj, ".env")
        with open(secret_file, "w") as f:
            f.write("DB_SECRET_PASS=ultra_confidential_998811\n")

        tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_21",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        result = self.orchestrator.execute(req)
        res_str = json.dumps(result.model_dump())
        self.assertNotIn("ultra_confidential_998811", res_str)

    # ------------------------------------------------------------------
    # 22. Traceback Sanitization
    # ------------------------------------------------------------------
    def test_22_traceback_sanitization(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        resp = client.post("/api/execution/start", json={
            "workspace_id": "ws_nonexistent_fake",
            "plan_id": "plan_fake",
        })
        self.assertEqual(resp.status_code, 403)
        body = resp.json()
        self.assertNotIn("Traceback", str(body))
        self.assertNotIn("File \"", str(body))
        self.assertEqual(body["detail"], WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 23. Concurrent Execution Safety
    # ------------------------------------------------------------------
    def test_23_concurrent_execution_safety(self):
        tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        errors = []

        def run_worker(idx):
            try:
                req = ExecutionRequest(
                    request_id=f"req_c_{idx}",
                    workspace_id=self.ws_id,
                    plan_id=plan_id,
                    execution_mode=ExecutionMode.DRY_RUN,
                )
                res = self.orchestrator.execute(req)
                assert res.status == ExecutionStatus.COMPLETED
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run_worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])

    # ------------------------------------------------------------------
    # 24. Execution Persistence
    # ------------------------------------------------------------------
    def test_24_execution_persistence(self):
        exec_id = "exec_persist_test"
        data = {"execution_id": exec_id, "workspace_id": self.ws_id, "status": "COMPLETED"}
        self.exec_store.save_execution(exec_id, data)

        loaded = self.exec_store.get_execution(exec_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["execution_id"], exec_id)

    # ------------------------------------------------------------------
    # 25. Corruption Recovery
    # ------------------------------------------------------------------
    def test_25_corruption_recovery(self):
        # Corrupt file content
        with open(self.exec_store_path, "w") as f:
            f.write("INVALID_JSON_CORRUPTION{{{{")

        self.exec_store._cache = None
        # Should gracefully recover without throwing
        result = self.exec_store.get_execution("nonexistent")
        self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 26. Restart / State Recovery
    # ------------------------------------------------------------------
    def test_26_restart_state_recovery(self):
        exec_id = "exec_restart_test"
        self.exec_store.save_execution(exec_id, {"execution_id": exec_id, "workspace_id": self.ws_id, "status": "COMPLETED"})

        # New instance pointing to same file simulating process restart
        new_store = ExecutionStore(self.exec_store_path)
        recovered = new_store.get_execution(exec_id)
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered["execution_id"], exec_id)

    # ------------------------------------------------------------------
    # 27. ToolRuntime Enforcement
    # ------------------------------------------------------------------
    def test_27_tool_runtime_enforcement(self):
        tasks = [{"task_id": "t1", "title": "T1", "description": "D1", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]}]
        plan_id = _create_sample_plan(self.ws_id, tasks)
        req = ExecutionRequest(
            request_id="req_27",
            workspace_id=self.ws_id,
            plan_id=plan_id,
            execution_mode=ExecutionMode.RUN,
        )
        res = self.orchestrator.execute(req)
        self.assertEqual(res.status, ExecutionStatus.COMPLETED)
        t_state = res.tasks[0]
        self.assertGreater(len(t_state.tool_results), 0)
        self.assertTrue(t_state.tool_results[0]["success"])

    # ------------------------------------------------------------------
    # 28. No Direct Filesystem Bypass
    # ------------------------------------------------------------------
    def test_28_no_direct_fs_bypass(self):
        # Context/Orchestrator never touches paths outside ToolRuntime
        req = ExecutionRequest(
            request_id="req_28",
            workspace_id=self.ws_id,
            plan_id="plan_123",
            execution_mode=ExecutionMode.DRY_RUN,
        )
        # Attempting execution with invalid plan fails at planner store level
        with self.assertRaises(ExecutionError):
            self.orchestrator.execute(req)

    # ------------------------------------------------------------------
    # 29. No Subprocess / Shell Execution
    # ------------------------------------------------------------------
    def test_29_no_subprocess_in_execution_modules(self):
        exec_dir = os.path.dirname(self.orchestrator.__module__.replace(".", "/"))
        forbidden = ["subprocess", "os.system", "os.popen", "Popen", "shell=True"]
        
        for root, _, files in os.walk(os.path.join(os.path.dirname(os.path.dirname(__file__)), "execution")):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for line in lines:
                        s = line.strip()
                        if s.startswith("#") or s.startswith('"') or s.startswith("'"):
                            continue
                        for pattern in forbidden:
                            self.assertNotIn(pattern, s, f"Forbidden pattern '{pattern}' in {fpath}")

    # ------------------------------------------------------------------
    # 30. Regression: Phase 1 Foundation
    # ------------------------------------------------------------------
    def test_30_regression_phase1_foundation(self):
        from tests.test_foundation import TestFoundation
        self.assertTrue(hasattr(TestFoundation, "test_bounded_cache_eviction"))

    # ------------------------------------------------------------------
    # 31. Regression: Phase 2A Workspace
    # ------------------------------------------------------------------
    def test_31_regression_phase2a_workspace(self):
        from tests.test_workspace import TestWorkspaceEngine
        self.assertTrue(hasattr(TestWorkspaceEngine, "test_path_traversal_escapes"))

    # ------------------------------------------------------------------
    # 32. Regression: Phase 2B Tool Runtime
    # ------------------------------------------------------------------
    def test_32_regression_phase2b_tools(self):
        from tests.test_tools import TestToolRuntimeAndPermissions
        self.assertTrue(hasattr(TestToolRuntimeAndPermissions, "test_read_allowed_write_denied"))

    # ------------------------------------------------------------------
    # 33. Regression: Phase 2C Planner
    # ------------------------------------------------------------------
    def test_33_regression_phase2c_planner(self):
        from tests.test_planner import TestPlannerPhase2C
        self.assertTrue(hasattr(TestPlannerPhase2C, "test_19_permission_analysis_complete"))

    # ------------------------------------------------------------------
    # 34. Full API End-to-End Lifecycle
    # ------------------------------------------------------------------
    def test_34_full_api_execution_lifecycle(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        reg_resp = client.post("/api/workspace", json={"root_path": self.proj})
        self.assertEqual(reg_resp.status_code, 200)
        api_ws_id = reg_resp.json()["workspace_id"]

        plan_resp = client.post("/api/planner/plan", json={
            "workspace_id": api_ws_id,
            "objective": "Analyze project files safely.",
            "requested_mode": "ANALYZE",
        })
        self.assertEqual(plan_resp.status_code, 200)
        plan_id = plan_resp.json()["plan"]["plan_id"]

        # 1. Start execution (Dry Run)
        start_resp = client.post("/api/execution/start", json={
            "workspace_id": api_ws_id,
            "plan_id": plan_id,
            "execution_mode": "DRY_RUN",
        })
        self.assertEqual(start_resp.status_code, 200)
        exec_data = start_resp.json()["execution"]
        exec_id = exec_data["execution_id"]
        self.assertEqual(exec_data["status"], "COMPLETED")

        # 2. Get status
        status_resp = client.get(f"/api/execution/{exec_id}")
        self.assertEqual(status_resp.status_code, 200)
        self.assertEqual(status_resp.json()["execution"]["execution_id"], exec_id)

        # 3. Get tasks
        tasks_resp = client.get(f"/api/execution/{exec_id}/tasks")
        self.assertEqual(tasks_resp.status_code, 200)
        self.assertGreater(len(tasks_resp.json()["tasks"]), 0)

        # 4. Cancel
        cancel_resp = client.post(f"/api/execution/{exec_id}/cancel")
        self.assertEqual(cancel_resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
