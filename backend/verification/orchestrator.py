"""
Phase 2F — Verification Orchestrator
Coordinates read-only verification across security, workspace, tests, integrity, regression, and health dimensions.
Enforces a strict fail-closed production readiness evaluation and emits structured audit logs.
"""
from __future__ import annotations
import uuid
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from workspace.store import WorkspaceStore
from verification.schemas import (
    VerificationRequest, VerificationResult, VerificationCheck,
    VerificationType, OverallVerificationStatus, ReadinessDecision
)
from verification.errors import (
    VerificationError,
    WORKSPACE_NOT_AUTHORIZED,
    VERIFICATION_NOT_FOUND,
)
from verification.security import SecurityInvariantChecker
from verification.workspace import WorkspaceVerifier
from verification.tests import TestVerifier
from verification.integrity import IntegrityVerifier
from verification.regression import RegressionDetector
from verification.health import RuntimeHealthChecker
from verification.readiness import ProductionReadinessEngine
from verification.audit import log_verification_audit
from verification.store import VerificationStore


class VerificationOrchestrator:
    """Core verification orchestrator executing read-only audits and readiness calculations."""

    def __init__(
        self,
        ws_store: Optional[WorkspaceStore] = None,
        ver_store: Optional[VerificationStore] = None,
    ):
        self._ws_store   = ws_store or WorkspaceStore()
        self._ver_store  = ver_store or VerificationStore()
        self._sec_check  = SecurityInvariantChecker()
        self._ws_check   = WorkspaceVerifier(self._ws_store)
        self._test_check = TestVerifier()
        self._integ_check = IntegrityVerifier()
        self._reg_check  = RegressionDetector()
        self._health_chk = RuntimeHealthChecker()
        self._readiness  = ProductionReadinessEngine()

    def run_verification(self, request: VerificationRequest) -> VerificationResult:
        """
        Executes read-only multi-dimension verification for a workspace.
        """
        start_time = time.perf_counter()
        verification_id = f"ver_{uuid.uuid4().hex[:10]}"

        # 1. Resolve Workspace
        ws_data = self._ws_store.get_workspace(request.workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise VerificationError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{request.workspace_id}' is not authorized.")
        workspace_root = ws_data["root_path"]

        checks: List[VerificationCheck] = []

        # 2. Security Invariants
        if request.include_security_checks:
            checks.extend(self._sec_check.verify_all_invariants())

        # 3. Workspace Containment & Traversal
        checks.extend(self._ws_check.verify_workspace(request.workspace_id))

        # 4. Test Coverage & Integrity
        if request.include_tests:
            checks.extend(self._test_check.verify_test_suites())

        # 5. Store & Plan/Execution/Modification Integrity
        if request.include_integrity_checks:
            checks.extend(self._integ_check.verify_workspace_integrity(
                workspace_id=request.workspace_id,
                workspace_root=workspace_root,
                plan_id=request.plan_id,
                execution_id=request.execution_id,
                modification_id=request.modification_id,
            ))

        # 6. Regression Detection
        checks.extend(self._reg_check.detect_regressions())

        # 7. Runtime Health
        if request.include_health_checks:
            checks.extend(self._health_chk.check_runtime_health())

        # 8. Readiness Evaluation
        overall_status, decision, sec_s, integ_s, test_s, ready_s, criticals, warnings, recs = (
            self._readiness.evaluate_readiness(checks)
        )

        dur_ms = (time.perf_counter() - start_time) * 1000

        # 9. Audit Record
        audit_ref = log_verification_audit(
            verification_id=verification_id,
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            status=overall_status.value,
            duration_ms=dur_ms,
            check_count=len(checks),
            critical_count=len(criticals),
            warning_count=len(warnings),
            readiness_decision=decision.value,
        )

        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        result = VerificationResult(
            verification_id=verification_id,
            workspace_id=request.workspace_id,
            status=overall_status,
            summary=f"Verification completed with {len(checks)} checks: {decision.value} (Readiness Score: {ready_s}/10).",
            checks=checks,
            security_score=sec_s,
            integrity_score=integ_s,
            test_score=test_s,
            readiness_score=ready_s,
            readiness_decision=decision,
            regressions=[],
            critical_findings=criticals,
            warnings=warnings,
            recommendations=recs,
            created_at=now_iso,
            completed_at=now_iso,
            duration_ms=round(dur_ms, 2),
            audit_reference=audit_ref,
        )

        # 10. Persist Result
        self._ver_store.save_verification(verification_id, result.model_dump())
        return result

    def get_verification(self, verification_id: str) -> Optional[VerificationResult]:
        """Loads verification result by ID."""
        data = self._ver_store.get_verification(verification_id)
        return VerificationResult(**data) if data else None
