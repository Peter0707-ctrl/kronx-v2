"""
Phase 2C — KronxPlanner (Core Orchestrator)
Wires together: workspace resolution, context building, task graph, risk engine,
reasoning, validation, audit logging, and plan persistence.

SECURITY INVARIANTS:
  - Never accesses workspace filesystem directly.
  - All tool calls go through ToolRuntime (never imported directly from here).
  - Sensitive file contents never enter planning context.
  - No subprocess, no os.system, no eval/exec.
  - Cannot self-grant permissions.
"""
from __future__ import annotations
import time
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from workspace.store import WorkspaceStore
from workspace.schema import ProjectProfile
from planner.schemas import (
    PlanningRequest, PlanningResult, PlanningMode,
    MAX_OBJECTIVE_LENGTH
)
from planner.context import ContextBuilder
from planner.task_graph import TaskGraph, PlanningGraphError
from planner.risk import RiskEngine
from planner.reasoning import ReasoningEngine
from planner.validator import PlanValidator, PlanValidationError
from planner.store import PlannerStore
from utils.logger import logger


class PlannerError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class KronxPlanner:
    """
    Core planning orchestrator.
    Accepts a PlanningRequest, produces a validated PlanningResult, and persists it.
    """

    def __init__(self):
        self._ws_store  = WorkspaceStore()
        self._risk      = RiskEngine()
        self._reasoning = ReasoningEngine()
        self._validator = PlanValidator()
        self._store     = PlannerStore()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def plan(self, request: PlanningRequest) -> PlanningResult:
        start = time.perf_counter()
        plan_id = f"plan_{uuid.uuid4().hex[:10]}"

        logger.info(
            f"[planner] plan_id={plan_id} request_id={request.request_id} "
            f"workspace={request.workspace_id} mode={request.requested_mode}"
        )

        # 1. Resolve workspace (server-side trusted lookup)
        ws_data = self._ws_store.get_workspace(request.workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise PlannerError("WORKSPACE_NOT_AUTHORIZED", "Workspace is not authorized.")

        # 2. Retrieve the latest Phase 2A ProjectProfile (if a scan has completed)
        profile: Optional[ProjectProfile] = self._get_profile(request.workspace_id)

        # 3. Build context (FACT / INFERENCE / ASSUMPTION) — no direct FS access
        ctx = ContextBuilder(profile, request.objective)
        facts, inferences, assumptions = ctx.build()
        summary = ctx.summary_for_mode(request.requested_mode)

        # 4. Generate mode-appropriate task skeleton
        raw_tasks = self._reasoning.build_tasks(
            request.requested_mode,
            request.objective,
            has_profile=profile is not None,
        )

        # 5. Build & validate task graph (catches cycles, duplicates, missing deps)
        try:
            graph = TaskGraph(raw_tasks)
            dep_graph = graph.dependency_graph()
        except PlanningGraphError as ge:
            raise PlannerError(ge.code, ge.detail)

        # 6. Risk evaluation
        risks, blocked_actions = self._risk.evaluate(request.objective, raw_tasks)

        # 7. Permission analysis
        permissions = self._reasoning.permission_analysis()

        # 8. Verification plan
        verification_plan = self._build_verification_plan(request.requested_mode)

        # 9. Confidence estimate
        confidence = self._estimate_confidence(profile, raw_tasks, risks)

        # 10. Assemble result
        duration_ms = (time.perf_counter() - start) * 1000
        result = PlanningResult(
            plan_id=plan_id,
            workspace_id=request.workspace_id,
            conversation_id=request.conversation_id,
            objective=request.objective,
            mode=request.requested_mode,
            summary=summary,
            assumptions=assumptions,
            facts=facts,
            inferences=inferences,
            tasks=raw_tasks,
            dependency_graph=dep_graph,
            risks=risks,
            required_permissions=permissions,
            blocked_actions=blocked_actions,
            verification_plan=verification_plan,
            confidence=confidence,
            status="COMPLETE",
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request_id=request.request_id,
            duration_ms=round(duration_ms, 2),
        )

        # 11. Validate plan (raises PlanValidationError on violation)
        try:
            self._validator.validate(result)
        except PlanValidationError as ve:
            raise PlannerError(ve.code, ve.detail)

        # 12. Persist
        self._store.save_plan(plan_id, result.model_dump())

        # 13. Audit log
        _ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        def _level_val(l):
            v = l.value if hasattr(l, "value") else str(l)
            try:
                return _ORDER.index(v)
            except ValueError:
                return 0
        top_risk = max((r.level for r in risks), key=_level_val, default="LOW")
        self._audit(
            plan_id=plan_id,
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            mode=str(request.requested_mode),
            status="COMPLETE",
            duration_ms=duration_ms,
            task_count=len(raw_tasks),
            risk_level=top_risk,
        )

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_profile(self, workspace_id: str) -> Optional[ProjectProfile]:
        """
        Retrieve the most recent completed scan profile from the workspace store.
        Returns None if no scan has completed.  Never reads the filesystem directly.
        """
        from workspace.store import WorkspaceStore
        ws_store = WorkspaceStore()
        try:
            data = ws_store._load_under_lock()
            jobs = data.get("jobs", {})
            completed = [
                j for j in jobs.values()
                if j.get("workspace_id") == workspace_id
                and j.get("status") == "COMPLETED"
                and j.get("result")
            ]
            if not completed:
                return None
            # Most recent completed job
            latest = max(completed, key=lambda j: j.get("started_at", ""))
            raw_result = latest["result"]
            return ProjectProfile(**raw_result)
        except Exception as e:
            logger.warning(f"[planner] Could not retrieve profile for {workspace_id}: {e}")
            return None

    def _build_verification_plan(self, mode: PlanningMode) -> list:
        mode_val = mode.value if hasattr(mode, "value") else mode
        base = [
            "Confirm all INSPECT tasks completed successfully.",
            "Review task dependency ordering matches expected execution flow.",
            "Verify no WRITE or EXECUTE capabilities were invoked.",
            "Confirm sensitive files were not read.",
        ]
        if mode_val in ("DESIGN", "REFACTOR", "DOCUMENT"):
            base.append("Obtain explicit user WRITE permission before file mutation.")
            base.append("Run full regression test suite after applying changes.")
        if mode_val == "DEBUG":
            base.append("Reproduce the bug with a minimal test case.")
            base.append("Confirm fix resolves the issue without regressions.")
        return base

    def _estimate_confidence(self, profile, tasks, risks) -> float:
        score = 0.5
        if profile is not None:
            score += 0.2
        if tasks:
            score += 0.1
        critical = sum(1 for r in risks if str(r.level) == "CRITICAL")
        score -= critical * 0.1
        return round(max(0.0, min(1.0, score)), 2)

    def _audit(self, **kwargs):
        """Write structured planner audit entry to application logger.  No secrets logged."""
        try:
            entry = {k: str(v) for k, v in kwargs.items()}
            logger.info(f"[planner_audit] {json.dumps(entry)}")
        except Exception:
            pass
