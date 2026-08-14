"""
Phase 3.1 — System Lifecycle Engine
Deterministic state machine managing STARTING -> READY -> DEGRADED -> DRAINING -> STOPPING -> STOPPED -> FAILED.
Tracks active jobs, handles request draining, and prevents unsafe actions during shutdown.
"""
import threading
from typing import Dict, Set, Optional
from datetime import datetime, timezone

from operations.schemas import LifecycleState, LifecycleStatus, EventType, Severity
from operations.errors import OperationsError, LIFECYCLE_INVALID_TRANSITION, SYSTEM_DRAINING, SYSTEM_STOPPED
from operations.store import OperationsStore
from operations.audit import log_operations_audit

_lifecycle_lock = threading.RLock()

# Permitted state transition map
VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
    LifecycleState.STARTING: {LifecycleState.READY, LifecycleState.FAILED},
    LifecycleState.READY:    {LifecycleState.DEGRADED, LifecycleState.DRAINING, LifecycleState.STOPPING, LifecycleState.FAILED},
    LifecycleState.DEGRADED: {LifecycleState.READY, LifecycleState.DRAINING, LifecycleState.STOPPING, LifecycleState.FAILED},
    LifecycleState.DRAINING: {LifecycleState.STOPPING, LifecycleState.READY, LifecycleState.FAILED},
    LifecycleState.STOPPING: {LifecycleState.STOPPED, LifecycleState.FAILED},
    LifecycleState.STOPPED:  {LifecycleState.STARTING, LifecycleState.READY},
    LifecycleState.FAILED:   {LifecycleState.STARTING, LifecycleState.DEGRADED, LifecycleState.READY},
}


class SystemLifecycleManager:
    def __init__(self, store: Optional[OperationsStore] = None):
        self._store = store or OperationsStore()
        self._state: LifecycleState = LifecycleState.READY
        self._active_jobs: Set[str] = set()
        self._started_at: str = datetime.now(timezone.utc).isoformat()
        self._updated_at: str = datetime.now(timezone.utc).isoformat()
        self._details: str = "System online and accepting requests."
        self._load_persisted_state()

    def _load_persisted_state(self) -> None:
        with _lifecycle_lock:
            data = self._store.get_lifecycle()
            state_str = data.get("state", "READY")
            try:
                self._state = LifecycleState(state_str)
            except ValueError:
                self._state = LifecycleState.READY
            self._started_at = data.get("started_at", self._started_at)
            self._details = data.get("details", self._details)

    def _persist_state(self) -> None:
        rec = {
            "state": self._state.value,
            "active_jobs": len(self._active_jobs),
            "draining": self._state == LifecycleState.DRAINING,
            "started_at": self._started_at,
            "updated_at": self._updated_at,
            "details": self._details,
        }
        self._store.save_lifecycle(rec)

    def get_status(self) -> LifecycleStatus:
        """Returns the current system lifecycle status."""
        with _lifecycle_lock:
            return LifecycleStatus(
                state=self._state,
                active_jobs=len(self._active_jobs),
                draining=self._state == LifecycleState.DRAINING,
                started_at=self._started_at,
                updated_at=self._updated_at,
                details=self._details,
            )

    def transition_to(self, target_state: LifecycleState, reason: str = "") -> LifecycleStatus:
        """Transitions to a new lifecycle state if the transition is valid."""
        with _lifecycle_lock:
            if target_state == self._state:
                return self.get_status()

            allowed = VALID_TRANSITIONS.get(self._state, set())
            if target_state not in allowed:
                raise OperationsError(
                    LIFECYCLE_INVALID_TRANSITION,
                    f"Invalid lifecycle transition from '{self._state.value}' to '{target_state.value}'."
                )

            old_state = self._state
            self._state = target_state
            self._updated_at = datetime.now(timezone.utc).isoformat()
            self._details = reason or f"Transitioned from {old_state.value} to {target_state.value}."
            self._persist_state()

            log_operations_audit(
                action="LIFECYCLE_TRANSITION",
                status="SUCCESS",
                details={"from": old_state.value, "to": target_state.value, "reason": self._details}
            )
            return self.get_status()

    def drain(self, reason: str = "Initiating system draining.") -> LifecycleStatus:
        """Puts the system into DRAINING mode, refusing new jobs while active jobs complete."""
        return self.transition_to(LifecycleState.DRAINING, reason=reason)

    def recover(self, reason: str = "Operational recovery invoked.") -> LifecycleStatus:
        """Recovers a DEGRADED, DRAINING, or FAILED system back to READY."""
        return self.transition_to(LifecycleState.READY, reason=reason)

    def stop(self, reason: str = "System stopped.") -> LifecycleStatus:
        """Stops the system."""
        with _lifecycle_lock:
            if self._state in [LifecycleState.READY, LifecycleState.DEGRADED, LifecycleState.DRAINING]:
                self.transition_to(LifecycleState.STOPPING, reason="Initiating shutdown.")
            return self.transition_to(LifecycleState.STOPPED, reason=reason)

    def register_job(self, job_id: str) -> None:
        """Registers a new active job. Fails closed if draining or stopped."""
        with _lifecycle_lock:
            if self._state == LifecycleState.DRAINING:
                raise OperationsError(SYSTEM_DRAINING, "System is currently draining. No new jobs accepted.")
            if self._state in [LifecycleState.STOPPING, LifecycleState.STOPPED, LifecycleState.FAILED]:
                raise OperationsError(SYSTEM_STOPPED, f"System is in '{self._state.value}' state. Cannot accept jobs.")
            self._active_jobs.add(job_id)
            self._persist_state()

    def unregister_job(self, job_id: str) -> None:
        """Unregisters a completed or cancelled active job."""
        with _lifecycle_lock:
            self._active_jobs.discard(job_id)
            self._persist_state()

    def is_accepting_work(self) -> bool:
        """Returns True if the system is in a state capable of processing new workloads."""
        with _lifecycle_lock:
            return self._state in [LifecycleState.READY, LifecycleState.DEGRADED]

    def reset_for_test(self) -> None:
        """Resets lifecycle state to READY (for tests)."""
        with _lifecycle_lock:
            self._state = LifecycleState.READY
            self._active_jobs.clear()
            self._updated_at = datetime.now(timezone.utc).isoformat()
            self._details = "System reset to READY."
            self._persist_state()
