"""
Phase 2C — Plan Validator
All plan validation with bounded resource limit enforcement.
"""
from __future__ import annotations
import json
from typing import Optional

from planner.schemas import PlanningResult, MAX_PLAN_SIZE_BYTES
from workspace.store import WorkspaceStore


class PlanValidationError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


class PlanValidator:
    """
    Validates a PlanningResult before it is persisted or returned.
    Does NOT modify the plan — raises PlanValidationError on any violation.
    """

    def __init__(self):
        self._ws_store = WorkspaceStore()

    def validate(self, result: PlanningResult) -> None:
        self._check_workspace(result.workspace_id)
        self._check_objective(result.objective)
        self._check_task_ids_unique(result)
        self._check_dependencies(result)
        self._check_size(result)
        self._check_no_sensitive_content(result)

    # ------------------------------------------------------------------

    def _check_workspace(self, workspace_id: str):
        ws = self._ws_store.get_workspace(workspace_id)
        if not ws or ws.get("status") != "authorized":
            raise PlanValidationError(
                "WORKSPACE_NOT_AUTHORIZED",
                f"Workspace '{workspace_id}' is not authorized."
            )

    def _check_objective(self, objective: str):
        if not objective or not objective.strip():
            raise PlanValidationError("EMPTY_OBJECTIVE", "Objective must not be empty.")

    def _check_task_ids_unique(self, result: PlanningResult):
        seen = set()
        for task in result.tasks:
            if task.task_id in seen:
                raise PlanValidationError(
                    "DUPLICATE_TASK_ID",
                    f"Duplicate task_id: '{task.task_id}'."
                )
            seen.add(task.task_id)

    def _check_dependencies(self, result: PlanningResult):
        task_ids = {t.task_id for t in result.tasks}
        for task in result.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise PlanValidationError(
                        "MISSING_DEPENDENCY",
                        f"Task '{task.task_id}' references unknown dep '{dep}'."
                    )

    def _check_size(self, result: PlanningResult):
        try:
            payload = json.dumps(result.model_dump(), default=str)
            size = len(payload.encode("utf-8"))
            if size > MAX_PLAN_SIZE_BYTES:
                raise PlanValidationError(
                    "PLAN_TOO_LARGE",
                    f"Serialised plan size {size} bytes exceeds limit of {MAX_PLAN_SIZE_BYTES} bytes."
                )
        except PlanValidationError:
            raise
        except Exception:
            pass  # serialisation guard; non-fatal if model_dump fails unexpectedly

    def _check_no_sensitive_content(self, result: PlanningResult):
        """
        Heuristic guard: reject plans that accidentally embed credential patterns.
        This is a last-resort safety net — the context builder should have prevented
        sensitive content from entering the plan in the first place.
        """
        _FORBIDDEN_PATTERNS = [
            "api_key=", "apikey=", "password=", "secret=",
            "private_key=", "-----BEGIN ", "aws_secret",
        ]
        # Serialize to string for scanning (no content read from workspace here)
        try:
            payload_lower = json.dumps(result.model_dump(), default=str).lower()
        except Exception:
            return
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern.lower() in payload_lower:
                raise PlanValidationError(
                    "SENSITIVE_CONTENT_DETECTED",
                    "Plan contains patterns that may represent sensitive credentials. "
                    "Planning rejected to prevent accidental leakage."
                )
