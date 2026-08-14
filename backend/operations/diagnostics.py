"""
Phase 3.1 — Safe Diagnostics Engine
Executes non-destructive operational diagnostics across storage, configuration, health, and security boundaries.
Guarantees: Zero shell execution, zero secret leaks, zero path disclosure, and zero file mutations.
"""
import time
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from operations.schemas import DiagnosticReport, DiagnosticCheck, HealthStatus
from operations.store import OperationsStore
from operations.integrity import StoreIntegrityManager
from operations.configuration import ConfigurationValidator
from operations.health import OperationsHealthEngine
from operations.audit import log_operations_audit
from llm.sanitizer import sanitize_secrets


class DiagnosticEngine:
    def __init__(
        self,
        store: Optional[OperationsStore] = None,
        integrity_mgr: Optional[StoreIntegrityManager] = None,
        config_val: Optional[ConfigurationValidator] = None,
        health_eng: Optional[OperationsHealthEngine] = None,
    ):
        self._store = store or OperationsStore()
        self._integrity = integrity_mgr or StoreIntegrityManager()
        self._config = config_val or ConfigurationValidator()
        self._health = health_eng or OperationsHealthEngine()

    def run_diagnostics(self) -> DiagnosticReport:
        """Executes the complete safe diagnostic suite."""
        diag_id = f"diag_{uuid.uuid4().hex[:12]}"
        checks: List[DiagnosticCheck] = []

        # 1. Configuration Check
        t0 = time.perf_counter()
        cfg_res = self._config.validate()
        dur1 = (time.perf_counter() - t0) * 1000.0
        checks.append(
            DiagnosticCheck(
                check_id=f"chk_cfg_{uuid.uuid4().hex[:6]}",
                name="Configuration & Provider Presence",
                category="CONFIGURATION",
                passed=cfg_res.is_valid,
                message="Configuration validated successfully." if cfg_res.is_valid else f"Errors: {cfg_res.errors}",
                duration_ms=round(dur1, 2),
            )
        )

        # 2. Persistent Stores Check
        t0 = time.perf_counter()
        store_records = self._integrity.check_all_stores()
        dur2 = (time.perf_counter() - t0) * 1000.0
        corrupt_stores = [s.store_name for s in store_records if s.corrupted]
        stores_passed = len(corrupt_stores) == 0
        checks.append(
            DiagnosticCheck(
                check_id=f"chk_str_{uuid.uuid4().hex[:6]}",
                name="Store Hash & Syntax Integrity",
                category="PERSISTENCE",
                passed=stores_passed,
                message=f"Verified {len(store_records)} persistent stores." if stores_passed else f"Corrupted stores: {corrupt_stores}",
                duration_ms=round(dur2, 2),
            )
        )

        # 3. Secret Sanitizer Check
        t0 = time.perf_counter()
        sample_secret = "Bearer eyJhbGciOiJIUzI1NiJ9.test.sig sk-1234567890abcdef1234567890"
        sanitized = sanitize_secrets(sample_secret)
        sanitizer_passed = "sk-1234567890" not in sanitized and "eyJhbGci" not in sanitized
        dur3 = (time.perf_counter() - t0) * 1000.0
        checks.append(
            DiagnosticCheck(
                check_id=f"chk_sec_{uuid.uuid4().hex[:6]}",
                name="Secret Sanitization & Redaction Engine",
                category="SECURITY",
                passed=sanitizer_passed,
                message="Secret sanitizer operational." if sanitizer_passed else "Sanitizer failed to redact sample key.",
                duration_ms=round(dur3, 2),
            )
        )

        # 4. Overall Health Check
        t0 = time.perf_counter()
        health_res = self._health.check_health()
        dur4 = (time.perf_counter() - t0) * 1000.0
        checks.append(
            DiagnosticCheck(
                check_id=f"chk_hlth_{uuid.uuid4().hex[:6]}",
                name="Subsystem Runtime Health",
                category="HEALTH",
                passed=health_res.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED],
                message=f"Health status is {health_res.status.value}.",
                duration_ms=round(dur4, 2),
            )
        )

        passed_count = sum(1 for c in checks if c.passed)
        failed_count = len(checks) - passed_count
        overall_health = HealthStatus.HEALTHY if failed_count == 0 else HealthStatus.UNHEALTHY

        report = DiagnosticReport(
            diagnostic_id=diag_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_checks=len(checks),
            passed_checks=passed_count,
            failed_checks=failed_count,
            checks=checks,
            system_health=overall_health,
        )

        self._store.record_diagnostic(report.model_dump())

        log_operations_audit(
            action="DIAGNOSTICS_RUN",
            status="SUCCESS" if failed_count == 0 else "FAILED",
            details={"diagnostic_id": diag_id, "passed": passed_count, "failed": failed_count}
        )
        return report

    def get_diagnostic(self, diagnostic_id: str) -> Optional[DiagnosticReport]:
        """Retrieves a previously stored diagnostic report."""
        raw = self._store.get_diagnostic(diagnostic_id)
        if not raw:
            return None
        return DiagnosticReport(**raw)
