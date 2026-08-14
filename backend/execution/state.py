"""
Phase 2D — Execution State Machine
Strict state transitions for execution workflows and individual tasks.
Lock-protected transitions and dependency propagation logic.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Set, Tuple

from execution.schemas import ExecutionStatus, TaskExecutionStatus
from execution.errors import ExecutionError, INVALID_EXECUTION_STATE

# ------------------------------------------------------------------
# Allowed State Transitions
# ------------------------------------------------------------------

VALID_EXECUTION_TRANSITIONS: Dict[ExecutionStatus, Set[ExecutionStatus]] = {
    ExecutionStatus.QUEUED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
        ExecutionStatus.BLOCKED,
    },
    ExecutionStatus.RUNNING: {
        ExecutionStatus.PAUSED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.BLOCKED,
    },
    ExecutionStatus.PAUSED: {
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    },
    ExecutionStatus.COMPLETED: set(),  # Terminal
    ExecutionStatus.FAILED:    set(),  # Terminal
    ExecutionStatus.CANCELLED: set(),  # Terminal
    ExecutionStatus.BLOCKED:   {
        ExecutionStatus.RUNNING,       # Can resume if permission granted
        ExecutionStatus.CANCELLED,
        ExecutionStatus.FAILED,
    },
}

VALID_TASK_TRANSITIONS: Dict[TaskExecutionStatus, Set[TaskExecutionStatus]] = {
    TaskExecutionStatus.PENDING: {
        TaskExecutionStatus.READY,
        TaskExecutionStatus.RUNNING,
        TaskExecutionStatus.BLOCKED,
        TaskExecutionStatus.SKIPPED,
        TaskExecutionStatus.CANCELLED,
    },
    TaskExecutionStatus.READY: {
        TaskExecutionStatus.RUNNING,
        TaskExecutionStatus.BLOCKED,
        TaskExecutionStatus.SKIPPED,
        TaskExecutionStatus.CANCELLED,
    },
    TaskExecutionStatus.RUNNING: {
        TaskExecutionStatus.COMPLETED,
        TaskExecutionStatus.FAILED,
        TaskExecutionStatus.BLOCKED,
        TaskExecutionStatus.CANCELLED,
    },
    TaskExecutionStatus.COMPLETED: set(),  # Terminal
    TaskExecutionStatus.FAILED:    {TaskExecutionStatus.RUNNING},  # Only on retry
    TaskExecutionStatus.BLOCKED:   {TaskExecutionStatus.READY, TaskExecutionStatus.RUNNING, TaskExecutionStatus.CANCELLED},
    TaskExecutionStatus.SKIPPED:   set(),  # Terminal
    TaskExecutionStatus.CANCELLED: set(),  # Terminal
}


class ExecutionStateMachine:
    """Thread-safe state transition manager and dependency evaluator."""

    def __init__(self):
        self._lock = threading.Lock()

    def validate_execution_transition(
        self,
        current: ExecutionStatus,
        target: ExecutionStatus
    ) -> None:
        """Check if execution transition is valid; raise ExecutionError if not."""
        with self._lock:
            allowed = VALID_EXECUTION_TRANSITIONS.get(current, set())
            if target not in allowed:
                raise ExecutionError(
                    INVALID_EXECUTION_STATE,
                    f"Invalid execution transition from '{current.value if hasattr(current, 'value') else current}' "
                    f"to '{target.value if hasattr(target, 'value') else target}'."
                )

    def validate_task_transition(
        self,
        current: TaskExecutionStatus,
        target: TaskExecutionStatus
    ) -> None:
        """Check if task transition is valid; raise ExecutionError if not."""
        with self._lock:
            allowed = VALID_TASK_TRANSITIONS.get(current, set())
            if target not in allowed:
                raise ExecutionError(
                    INVALID_EXECUTION_STATE,
                    f"Invalid task transition from '{current.value if hasattr(current, 'value') else current}' "
                    f"to '{target.value if hasattr(target, 'value') else target}'."
                )

    @staticmethod
    def evaluate_task_readiness(
        task_id: str,
        dependencies: List[str],
        task_statuses: Dict[str, TaskExecutionStatus]
    ) -> Tuple[TaskExecutionStatus, str]:
        """
        Evaluate if a task is READY, BLOCKED, or SKIPPED based on upstream dependencies.
        Returns (new_status, reason).
        """
        if not dependencies:
            return TaskExecutionStatus.READY, "No dependencies."

        for dep_id in dependencies:
            dep_status = task_statuses.get(dep_id, TaskExecutionStatus.PENDING)
            
            # If any dependency failed, downstream task is SKIPPED/BLOCKED
            if dep_status == TaskExecutionStatus.FAILED:
                return TaskExecutionStatus.SKIPPED, f"Prerequisite dependency '{dep_id}' failed."
            if dep_status in (TaskExecutionStatus.BLOCKED, TaskExecutionStatus.SKIPPED, TaskExecutionStatus.CANCELLED):
                return TaskExecutionStatus.BLOCKED, f"Prerequisite dependency '{dep_id}' is '{dep_status.value}'."
            if dep_status != TaskExecutionStatus.COMPLETED:
                return TaskExecutionStatus.PENDING, f"Prerequisite dependency '{dep_id}' is not completed ({dep_status.value})."

        return TaskExecutionStatus.READY, "All prerequisite dependencies completed."
