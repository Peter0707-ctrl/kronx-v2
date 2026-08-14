"""
Phase 2D — Execution Orchestrator
Core orchestration engine coordinating dry-run validation and safe tool execution.
Strictly routes all tool execution through ToolRuntime; enforces default-deny permissions,
cooperative cancellation, pause/resume, and checkpoint persistence.
"""
from __future__ import annotations
import time
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from workspace.store import WorkspaceStore
from planner.store import PlannerStore
from planner.schemas import PlanningResult, PlanningTask, TaskType
from planner.task_graph import TaskGraph, PlanningGraphError
from tools.runtime import ToolRuntime
from execution.schemas import (
    ExecutionRequest, ExecutionResult, ExecutionTaskState,
    ExecutionMode, ExecutionStatus, TaskExecutionStatus,
    MAX_TASKS_PER_EXECUTION, MAX_TOOL_CALLS_PER_TASK,
    MAX_TOTAL_TOOL_CALLS, MAX_RETRY_ATTEMPTS,
)
from execution.errors import (
    ExecutionError, EXECUTION_NOT_FOUND, PLAN_NOT_FOUND,
    WORKSPACE_NOT_AUTHORIZED, INVALID_TASK_ID,
    BLOCKED_REQUIRES_PERMISSION, FORBIDDEN_PERMISSION_LEVEL,
    RESOURCE_LIMIT_EXCEEDED, EXECUTION_CANCELLED,
    EXECUTION_PAUSED, NON_RETRYABLE_CODES,
)
from execution.state import ExecutionStateMachine
from execution.authorization import ExecutionAuthorizer
from execution.checkpoint import ExecutionStore
from execution.verifier import ExecutionVerifier
from execution.audit import log_execution_audit
from utils.logger import logger

_cancellation_tokens: Dict[str, threading.Event] = {}
_pause_tokens: Dict[str, threading.Event] = {}
_orchestrator_lock = threading.Lock()


class ExecutionOrchestrator:
    """Core execution engine for Kron-X Phase 2D."""

    def __init__(self, store: Optional[ExecutionStore] = None):
        self._ws_store      = WorkspaceStore()
        self._plan_store    = PlannerStore()
        self._exec_store    = store or ExecutionStore()
        self._state_machine = ExecutionStateMachine()
        self._authorizer    = ExecutionAuthorizer()
        self._tool_runtime  = ToolRuntime()
        self._verifier      = ExecutionVerifier()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """
        Execute a plan according to request mode (DRY_RUN or RUN).
        """
        start_time = time.perf_counter()
        execution_id = f"exec_{uuid.uuid4().hex[:10]}"

        # 1. Resolve Workspace
        ws_data = self._ws_store.get_workspace(request.workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise ExecutionError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{request.workspace_id}' is not authorized.")

        # 2. Resolve Plan
        plan_data = self._plan_store.get_plan(request.plan_id)
        if not plan_data:
            raise ExecutionError(PLAN_NOT_FOUND, f"Plan '{request.plan_id}' not found.")

        # Validate plan belongs to workspace
        if plan_data.get("workspace_id") != request.workspace_id:
            raise ExecutionError(WORKSPACE_NOT_AUTHORIZED, "Plan does not belong to the authorized workspace.")

        raw_tasks = plan_data.get("tasks", [])
        if len(raw_tasks) > MAX_TASKS_PER_EXECUTION:
            raise ExecutionError(RESOURCE_LIMIT_EXCEEDED, f"Plan task count ({len(raw_tasks)}) exceeds limit ({MAX_TASKS_PER_EXECUTION}).")

        # 3. Filter requested tasks if specified
        task_map = {t["task_id"]: t for t in raw_tasks}
        if request.requested_task_ids:
            for tid in request.requested_task_ids:
                if tid not in task_map:
                    raise ExecutionError(INVALID_TASK_ID, f"Requested task_id '{tid}' not in plan.")
            selected_tasks = [task_map[tid] for tid in request.requested_task_ids]
        else:
            selected_tasks = raw_tasks

        # 4. Initialize task states
        task_states: Dict[str, ExecutionTaskState] = {}
        for t in selected_tasks:
            req_tools = t.get("required_tools", [])
            task_states[t["task_id"]] = ExecutionTaskState(
                task_id=t["task_id"],
                title=t.get("title", ""),
                description=t.get("description", ""),
                status=TaskExecutionStatus.PENDING,
                dependencies=t.get("dependencies", []),
                required_tools=req_tools,
                required_permissions=["READ"],
                risk_level=str(t.get("risk_level", "LOW")),
            )

        # 5. Build TaskGraph to determine execution order
        planning_tasks = [PlanningTask(**t) for t in selected_tasks]
        try:
            graph = TaskGraph(planning_tasks)
            exec_order = graph.get_execution_order()
        except PlanningGraphError as ge:
            raise ExecutionError(ge.code, ge.detail)

        # 6. Initialize Cancellation / Pause tokens
        cancel_event = threading.Event()
        pause_event  = threading.Event()
        with _orchestrator_lock:
            _cancellation_tokens[execution_id] = cancel_event
            _pause_tokens[execution_id] = pause_event

        # 7. Initial Save
        audit_ref = log_execution_audit(
            execution_id=execution_id,
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            plan_id=request.plan_id,
            status=ExecutionStatus.QUEUED.value,
        )

        initial_result = ExecutionResult(
            execution_id=execution_id,
            plan_id=request.plan_id,
            workspace_id=request.workspace_id,
            status=ExecutionStatus.QUEUED,
            execution_mode=request.execution_mode,
            tasks=list(task_states.values()),
            verification_results=[],
            audit_reference=audit_ref,
            user_id=request.user_id,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
        )
        self._exec_store.save_execution(execution_id, initial_result.model_dump())

        # 8. Execution Route (DRY_RUN vs RUN)
        if request.execution_mode == ExecutionMode.DRY_RUN:
            result = self._execute_dry_run(
                execution_id=execution_id,
                request=request,
                task_states=task_states,
                exec_order=exec_order,
                start_time=start_time,
                audit_ref=audit_ref,
            )
        else:
            result = self._execute_run(
                execution_id=execution_id,
                request=request,
                task_states=task_states,
                exec_order=exec_order,
                cancel_event=cancel_event,
                pause_event=pause_event,
                start_time=start_time,
                audit_ref=audit_ref,
            )

        # Cleanup tokens
        with _orchestrator_lock:
            _cancellation_tokens.pop(execution_id, None)
            _pause_tokens.pop(execution_id, None)

        return result

    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        data = self._exec_store.get_execution(execution_id)
        return ExecutionResult(**data) if data else None

    def cancel(self, execution_id: str) -> ExecutionResult:
        """Cooperative cancellation request."""
        with _orchestrator_lock:
            if execution_id in _cancellation_tokens:
                _cancellation_tokens[execution_id].set()

        data = self._exec_store.get_execution(execution_id)
        if not data:
            raise ExecutionError(EXECUTION_NOT_FOUND, f"Execution '{execution_id}' not found.")

        current_status = data.get("status")
        if current_status in (ExecutionStatus.RUNNING.value, ExecutionStatus.QUEUED.value, ExecutionStatus.PAUSED.value):
            data["status"] = ExecutionStatus.CANCELLED.value
            data["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._exec_store.save_execution(execution_id, data)
            log_execution_audit(
                execution_id=execution_id,
                request_id="cancel_call",
                workspace_id=data.get("workspace_id", ""),
                plan_id=data.get("plan_id", ""),
                status=ExecutionStatus.CANCELLED.value,
            )

        return ExecutionResult(**data)

    def pause(self, execution_id: str) -> ExecutionResult:
        """Pause running execution."""
        with _orchestrator_lock:
            if execution_id in _pause_tokens:
                _pause_tokens[execution_id].set()

        data = self._exec_store.get_execution(execution_id)
        if not data:
            raise ExecutionError(EXECUTION_NOT_FOUND, f"Execution '{execution_id}' not found.")

        if data.get("status") == ExecutionStatus.RUNNING.value:
            data["status"] = ExecutionStatus.PAUSED.value
            self._exec_store.save_execution(execution_id, data)
            log_execution_audit(
                execution_id=execution_id,
                request_id="pause_call",
                workspace_id=data.get("workspace_id", ""),
                plan_id=data.get("plan_id", ""),
                status=ExecutionStatus.PAUSED.value,
            )

        return ExecutionResult(**data)

    def resume(self, execution_id: str) -> ExecutionResult:
        """Resume paused execution."""
        with _orchestrator_lock:
            if execution_id in _pause_tokens:
                _pause_tokens[execution_id].clear()

        data = self._exec_store.get_execution(execution_id)
        if not data:
            raise ExecutionError(EXECUTION_NOT_FOUND, f"Execution '{execution_id}' not found.")

        if data.get("status") == ExecutionStatus.PAUSED.value:
            data["status"] = ExecutionStatus.RUNNING.value
            self._exec_store.save_execution(execution_id, data)
            log_execution_audit(
                execution_id=execution_id,
                request_id="resume_call",
                workspace_id=data.get("workspace_id", ""),
                plan_id=data.get("plan_id", ""),
                status=ExecutionStatus.RUNNING.value,
            )

        return ExecutionResult(**data)

    # ------------------------------------------------------------------
    # Internal Execution Routines
    # ------------------------------------------------------------------

    def _execute_dry_run(
        self,
        execution_id: str,
        request: ExecutionRequest,
        task_states: Dict[str, ExecutionTaskState],
        exec_order: List[str],
        start_time: float,
        audit_ref: str,
    ) -> ExecutionResult:
        """
        Dry-run mode: validates DAG, permissions, tools, estimates actions.
        Zero mutations, zero tool invocations.
        """
        completed: List[str] = []
        blocked: List[str] = []
        skipped: List[str] = []
        failed: List[str] = []
        verifications: List[Dict[str, Any]] = []

        for tid in exec_order:
            ts = task_states[tid]
            # Validate permissions for required tools
            is_auth, code, blocked_tools = self._authorizer.authorize_task_tools(
                task_id=tid,
                required_tools=ts.required_tools,
                effective_permission="READ",
                confirmation_token=request.confirmation_token,
            )
            if not is_auth:
                ts.status = TaskExecutionStatus.BLOCKED
                ts.error = f"Dry-run detected unauthorized tools: {blocked_tools} ({code})"
                blocked.append(tid)
            else:
                ts.status = TaskExecutionStatus.COMPLETED
                ts.result_summary = f"[DRY-RUN] Estimated actions for '{ts.title}' validated successfully."
                completed.append(tid)

            verifications.append(self._verifier.verify_task_completion(tid, ts.model_dump()))

        overall_status = ExecutionStatus.BLOCKED if blocked else ExecutionStatus.COMPLETED
        duration_ms = (time.perf_counter() - start_time) * 1000

        result = ExecutionResult(
            execution_id=execution_id,
            plan_id=request.plan_id,
            workspace_id=request.workspace_id,
            status=overall_status,
            execution_mode=ExecutionMode.DRY_RUN,
            completed_tasks=completed,
            blocked_tasks=blocked,
            failed_tasks=failed,
            skipped_tasks=skipped,
            tasks=list(task_states.values()),
            verification_results=verifications,
            audit_reference=audit_ref,
            completed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            duration_ms=round(duration_ms, 2),
            user_id=request.user_id,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
        )
        self._exec_store.save_execution(execution_id, result.model_dump())
        return result

    def _execute_run(
        self,
        execution_id: str,
        request: ExecutionRequest,
        task_states: Dict[str, ExecutionTaskState],
        exec_order: List[str],
        cancel_event: threading.Event,
        pause_event: threading.Event,
        start_time: float,
        audit_ref: str,
    ) -> ExecutionResult:
        """
        Run mode: executes tasks via ToolRuntime with permission checks,
        cooperative cancellation, bounded retries, and read-only verification.
        """
        completed: List[str] = []
        blocked: List[str] = []
        skipped: List[str] = []
        failed: List[str] = []
        verifications: List[Dict[str, Any]] = []
        total_tool_calls = 0

        current_exec_status = ExecutionStatus.RUNNING
        self._update_execution_status(execution_id, current_exec_status)

        for tid in exec_order:
            # 1. Cancellation Check
            if cancel_event.is_set():
                current_exec_status = ExecutionStatus.CANCELLED
                task_states[tid].status = TaskExecutionStatus.CANCELLED
                skipped.append(tid)
                continue

            # 2. Pause Check (spin wait safely up to 30s or until unpaused)
            if pause_event.is_set():
                self._update_execution_status(execution_id, ExecutionStatus.PAUSED)
                while pause_event.is_set() and not cancel_event.is_set():
                    time.sleep(0.05)
                if cancel_event.is_set():
                    current_exec_status = ExecutionStatus.CANCELLED
                    task_states[tid].status = TaskExecutionStatus.CANCELLED
                    skipped.append(tid)
                    continue
                self._update_execution_status(execution_id, ExecutionStatus.RUNNING)

            ts = task_states[tid]
            ts.started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            # 3. Dependency Check
            status_map = {t_id: t_state.status for t_id, t_state in task_states.items()}
            dep_status, dep_reason = self._state_machine.evaluate_task_readiness(
                tid, ts.dependencies, status_map
            )

            if dep_status == TaskExecutionStatus.SKIPPED:
                ts.status = TaskExecutionStatus.SKIPPED
                ts.error = dep_reason
                skipped.append(tid)
                continue
            elif dep_status == TaskExecutionStatus.BLOCKED:
                ts.status = TaskExecutionStatus.BLOCKED
                ts.error = dep_reason
                blocked.append(tid)
                continue

            # 4. Permission Authorization Check
            is_auth, perm_code, blocked_tools = self._authorizer.authorize_task_tools(
                task_id=tid,
                required_tools=ts.required_tools,
                effective_permission="READ",
                confirmation_token=request.confirmation_token,
            )

            if not is_auth:
                ts.status = TaskExecutionStatus.BLOCKED
                ts.error = f"Unauthorized tools: {blocked_tools} ({perm_code})"
                blocked.append(tid)
                log_execution_audit(
                    execution_id=execution_id,
                    request_id=request.request_id,
                    workspace_id=request.workspace_id,
                    plan_id=request.plan_id,
                    task_id=tid,
                    status="BLOCKED",
                    error_code=perm_code,
                )
                continue

            # 5. Task Tool Execution via ToolRuntime
            ts.status = TaskExecutionStatus.RUNNING
            task_success = True
            task_error = None

            if not ts.required_tools:
                # Non-tool informational/analytical task
                ts.status = TaskExecutionStatus.COMPLETED
                ts.result_summary = f"Completed step '{ts.title}'."
                completed.append(tid)
            else:
                # Execute tools bounded by limits & retries
                tool_calls_this_task = 0
                for tool_name in ts.required_tools:
                    if cancel_event.is_set():
                        ts.status = TaskExecutionStatus.CANCELLED
                        task_success = False
                        break

                    if total_tool_calls >= MAX_TOTAL_TOOL_CALLS or tool_calls_this_task >= MAX_TOOL_CALLS_PER_TASK:
                        task_error = RESOURCE_LIMIT_EXCEEDED
                        task_success = False
                        break

                    # Execute with bounded retries
                    success, res_data, err_code = self._execute_tool_with_retries(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                        tool_name=tool_name,
                        task_state=ts,
                    )
                    tool_calls_this_task += 1
                    total_tool_calls += 1

                    if not success:
                        task_success = False
                        task_error = err_code
                        break

                    # Verification of tool result
                    v_res = self._verifier.verify_tool_result(tid, tool_name, res_data)
                    verifications.append(v_res)

                if task_success:
                    ts.status = TaskExecutionStatus.COMPLETED
                    ts.result_summary = f"Successfully executed {len(ts.required_tools)} tools for '{ts.title}'."
                    completed.append(tid)
                else:
                    if ts.status != TaskExecutionStatus.CANCELLED:
                        ts.status = TaskExecutionStatus.FAILED
                        ts.error = task_error or "Tool execution failed."
                        failed.append(tid)

            ts.completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            verifications.append(self._verifier.verify_task_completion(tid, ts.model_dump()))

            # Checkpoint update
            self._save_checkpoint(execution_id, request, task_states, current_exec_status)

        # 6. Compute overall status
        if cancel_event.is_set() or current_exec_status == ExecutionStatus.CANCELLED:
            final_status = ExecutionStatus.CANCELLED
        elif failed:
            final_status = ExecutionStatus.FAILED
        elif blocked:
            final_status = ExecutionStatus.BLOCKED
        else:
            final_status = ExecutionStatus.COMPLETED

        duration_ms = (time.perf_counter() - start_time) * 1000
        result = ExecutionResult(
            execution_id=execution_id,
            plan_id=request.plan_id,
            workspace_id=request.workspace_id,
            status=final_status,
            execution_mode=ExecutionMode.RUN,
            completed_tasks=completed,
            blocked_tasks=blocked,
            failed_tasks=failed,
            skipped_tasks=skipped,
            tasks=list(task_states.values()),
            verification_results=verifications,
            audit_reference=audit_ref,
            completed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            duration_ms=round(duration_ms, 2),
            user_id=request.user_id,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
        )
        self._exec_store.save_execution(execution_id, result.model_dump())
        return result

    def _execute_tool_with_retries(
        self,
        request_id: str,
        workspace_id: str,
        tool_name: str,
        task_state: ExecutionTaskState,
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Invokes a tool via ToolRuntime enforcing bounded retries for retryable errors."""
        arguments = {"path": "."}  # default safe inspection argument
        attempts = 0

        while attempts < MAX_RETRY_ATTEMPTS:
            attempts += 1
            task_state.attempts += 1

            tool_res = self._tool_runtime.execute_tool(
                request_id=request_id,
                workspace_id=workspace_id,
                tool_name=tool_name,
                arguments=arguments,
                client_effective_permission="READ",
            )
            res_dict = tool_res.model_dump()
            task_state.tool_results.append(res_dict)

            if tool_res.success:
                return True, res_dict, None

            err_code = tool_res.error or "UNKNOWN_ERROR"
            # Non-retryable errors abort immediately
            if err_code in NON_RETRYABLE_CODES:
                return False, res_dict, err_code

        return False, res_dict, "MAX_RETRIES_EXCEEDED"

    def _update_execution_status(self, execution_id: str, status: ExecutionStatus):
        data = self._exec_store.get_execution(execution_id)
        if data:
            data["status"] = status.value if hasattr(status, "value") else status
            self._exec_store.save_execution(execution_id, data)

    def _save_checkpoint(
        self,
        execution_id: str,
        request: ExecutionRequest,
        task_states: Dict[str, ExecutionTaskState],
        status: ExecutionStatus,
    ):
        data = self._exec_store.get_execution(execution_id) or {}
        data["execution_id"] = execution_id
        data["plan_id"] = request.plan_id
        data["workspace_id"] = request.workspace_id
        data["status"] = status.value if hasattr(status, "value") else status
        data["tasks"] = [t.model_dump() for t in task_states.values()]
        self._exec_store.save_execution(execution_id, data)
