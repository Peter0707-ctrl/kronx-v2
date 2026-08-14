"""
Phase 2H — Concurrency Protection Engine
Enforces bounded thread and execution semaphores across all expensive Kron-X operations.
"""
from __future__ import annotations
import threading
from contextlib import contextmanager
from config.settings import config
from gateway.errors import GatewayError, CONCURRENCY_LIMIT


class ConcurrencyCoordinator:
    """Manages bounded concurrency semaphores for system tasks."""

    def __init__(self):
        self._semaphores = {
            "SCAN": threading.BoundedSemaphore(config.max_concurrent_scans),
            "PLAN": threading.BoundedSemaphore(config.max_concurrent_plans),
            "EXECUTION": threading.BoundedSemaphore(config.max_concurrent_executions),
            "MODIFICATION": threading.BoundedSemaphore(config.max_concurrent_modifications),
            "VERIFICATION": threading.BoundedSemaphore(config.max_concurrent_verifications),
        }

    @contextmanager
    def limit_concurrency(self, operation: str, timeout: float = 0.05):
        """
        Context manager to acquire a concurrency slot for an operation.
        Raises GatewayError(CONCURRENCY_LIMIT) if capacity is full.
        """
        op = operation.upper()
        sem = self._semaphores.get(op)
        if not sem:
            yield
            return

        acquired = sem.acquire(timeout=timeout)
        if not acquired:
            raise GatewayError(
                code=CONCURRENCY_LIMIT,
                detail=f"System is processing maximum concurrent {op} operations. Please retry shortly.",
                status_code=429,
            )
        try:
            yield
        finally:
            sem.release()


concurrency_coordinator = ConcurrencyCoordinator()
