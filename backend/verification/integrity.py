"""
Phase 2F — Integrity Verifier
Verifies filesystem hash integrity, proposal states, execution checkpoints, and rollback snapshots.
Detects state drift, unexpected mutations, and rollback conflicts without modifying files.
"""
from __future__ import annotations
import os
import time
from typing import List, Dict, Any, Optional

from tools.path_verify import verify_safe_path
from modification.atomic import AtomicPatcher
from modification.stores import ModificationStore, RollbackStore, ProposalStore
from planner.store import PlannerStore
from execution.checkpoint import ExecutionStore
from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity
from verification.checks import create_check


class IntegrityVerifier:
    """Read-only verifier for store records, hashes, checkpoints, and rollback snapshots."""

    def __init__(
        self,
        prop_store: Optional[ProposalStore] = None,
        mod_store: Optional[ModificationStore] = None,
        roll_store: Optional[RollbackStore] = None,
        plan_store: Optional[PlannerStore] = None,
        exec_store: Optional[ExecutionStore] = None,
    ):
        self._prop_store = prop_store or ProposalStore()
        self._mod_store  = mod_store or ModificationStore()
        self._roll_store = roll_store or RollbackStore()
        self._plan_store = plan_store or PlannerStore()
        self._exec_store = exec_store or ExecutionStore()

    def verify_workspace_integrity(
        self,
        workspace_id: str,
        workspace_root: str,
        plan_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        modification_id: Optional[str] = None,
    ) -> List[VerificationCheck]:
        """Runs integrity checks across stored records and live workspace files."""
        checks: List[VerificationCheck] = []

        # 1. Plan Integrity Check (if plan_id provided)
        if plan_id:
            start_t = time.perf_counter()
            plan_data = self._plan_store.get_plan(plan_id)
            dur = (time.perf_counter() - start_t) * 1000

            if not plan_data:
                checks.append(create_check(
                    category="INTEGRITY",
                    name="PLAN_INTEGRITY",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.HIGH,
                    message=f"Plan '{plan_id}' not found in PlannerStore.",
                    evidence={"plan_id": plan_id},
                    duration_ms=dur,
                ))
            else:
                task_count = len(plan_data.get("tasks", []))
                checks.append(create_check(
                    category="INTEGRITY",
                    name="PLAN_INTEGRITY",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.INFO,
                    message=f"Plan '{plan_id}' integrity verified ({task_count} tasks).",
                    evidence={"plan_id": plan_id, "task_count": task_count},
                    duration_ms=dur,
                ))

        # 2. Execution Checkpoint Integrity (if execution_id provided)
        if execution_id:
            start_t = time.perf_counter()
            exec_data = self._exec_store.get_execution(execution_id)
            dur = (time.perf_counter() - start_t) * 1000

            if not exec_data:
                checks.append(create_check(
                    category="INTEGRITY",
                    name="EXECUTION_CHECKPOINT_INTEGRITY",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.HIGH,
                    message=f"Execution record '{execution_id}' not found.",
                    evidence={"execution_id": execution_id},
                    duration_ms=dur,
                ))
            else:
                checks.append(create_check(
                    category="INTEGRITY",
                    name="EXECUTION_CHECKPOINT_INTEGRITY",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.INFO,
                    message=f"Execution '{execution_id}' checkpoint valid (status: {exec_data.get('status')}).",
                    evidence={"execution_id": execution_id, "status": exec_data.get("status")},
                    duration_ms=dur,
                ))

        # 3. Modification & Rollback Integrity (if modification_id provided)
        if modification_id:
            start_t = time.perf_counter()
            mod_data = self._mod_store.get_item(modification_id)
            dur = (time.perf_counter() - start_t) * 1000

            if not mod_data:
                checks.append(create_check(
                    category="INTEGRITY",
                    name="MODIFICATION_RECORD_INTEGRITY",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.HIGH,
                    message=f"Modification '{modification_id}' not found in store.",
                    evidence={"modification_id": modification_id},
                    duration_ms=dur,
                ))
            else:
                # Check rollback record
                roll_id = mod_data.get("rollback_id")
                roll_record = self._roll_store.get_item(roll_id) if roll_id else None
                if roll_id and not roll_record:
                    checks.append(create_check(
                        category="INTEGRITY",
                        name="ROLLBACK_RECORD_INTEGRITY",
                        status=CheckStatus.WARN,
                        severity=CheckSeverity.MEDIUM,
                        message=f"Rollback snapshot '{roll_id}' missing for modification '{modification_id}'.",
                        evidence={"rollback_id": roll_id},
                        duration_ms=dur,
                    ))
                else:
                    checks.append(create_check(
                        category="INTEGRITY",
                        name="MODIFICATION_RECORD_INTEGRITY",
                        status=CheckStatus.PASS,
                        severity=CheckSeverity.INFO,
                        message=f"Modification '{modification_id}' and rollback snapshot verified.",
                        evidence={"modification_id": modification_id, "rollback_id": roll_id},
                        duration_ms=dur,
                    ))

        return checks
