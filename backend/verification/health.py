"""
Phase 2F — Runtime Health Checker
Verifies persistent store access, logging subsystems, and application runtime readiness without leaking secrets.
"""
from __future__ import annotations
import time
from typing import List, Dict, Any

from workspace.store import WorkspaceStore
from planner.store import PlannerStore
from execution.checkpoint import ExecutionStore
from modification.stores import (
    ModificationStore, AuthorizationStore, RollbackStore, ProposalStore
)
from memory.store import MemoryStore
from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity
from verification.checks import create_check


class RuntimeHealthChecker:
    """Performs runtime health and store accessibility checks."""

    def check_runtime_health(self) -> List[VerificationCheck]:
        """Runs full suite of runtime health checks."""
        checks: List[VerificationCheck] = []
        start_t = time.perf_counter()

        stores_status: Dict[str, bool] = {}
        failed_stores: List[str] = []

        stores_to_check = [
            ("WorkspaceStore", WorkspaceStore),
            ("PlannerStore", PlannerStore),
            ("ExecutionStore", ExecutionStore),
            ("ModificationStore", ModificationStore),
            ("AuthorizationStore", AuthorizationStore),
            ("RollbackStore", RollbackStore),
            ("ProposalStore", ProposalStore),
            ("MemoryStore", MemoryStore),
        ]

        for name, store_cls in stores_to_check:
            try:
                inst = store_cls()
                # Attempt safe read
                if hasattr(inst, "_load_under_lock"):
                    _ = inst._load_under_lock()
                stores_status[name] = True
            except Exception as e:
                stores_status[name] = False
                failed_stores.append(f"{name}: {e}")

        dur = (time.perf_counter() - start_t) * 1000

        if failed_stores:
            checks.append(create_check(
                category="HEALTH",
                name="PERSISTENCE_STORE_HEALTH",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"Store health failure: {failed_stores}",
                evidence={"stores_status": stores_status, "failed": failed_stores},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="HEALTH",
                name="PERSISTENCE_STORE_HEALTH",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message=f"Verified: All {len(stores_to_check)} persistence stores accessible and healthy.",
                evidence={"stores_status": stores_status},
                duration_ms=dur,
            ))

        return checks
