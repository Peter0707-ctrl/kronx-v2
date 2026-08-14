"""
Phase 3.1 — Operations Readiness Engine
Fail-closed production readiness evaluator.
Assesses security boundaries, store integrity, configuration, health, and lifecycle.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from operations.schemas import ReadinessDecision, ReadinessEvaluation, HealthStatus, LifecycleState
from operations.health import OperationsHealthEngine
from operations.configuration import ConfigurationValidator
from operations.integrity import StoreIntegrityManager
from operations.lifecycle import SystemLifecycleManager


class OperationsReadinessEngine:
    def __init__(
        self,
        health_engine: Optional[OperationsHealthEngine] = None,
        config_validator: Optional[ConfigurationValidator] = None,
        integrity_manager: Optional[StoreIntegrityManager] = None,
        lifecycle_manager: Optional[SystemLifecycleManager] = None,
    ):
        self._health = health_engine or OperationsHealthEngine()
        self._config = config_validator or ConfigurationValidator()
        self._integrity = integrity_manager or StoreIntegrityManager()
        self._lifecycle = lifecycle_manager or SystemLifecycleManager()

    def evaluate_readiness(self) -> ReadinessEvaluation:
        """Conducts exhaustive readiness evaluation and returns a fail-closed decision."""
        checks: List[Dict[str, Any]] = []
        critical_count = 0
        warning_count = 0

        # 1. Lifecycle State
        lc = self._lifecycle.get_status()
        if lc.state == LifecycleState.READY:
            checks.append({"name": "lifecycle", "status": "PASS", "detail": f"State is {lc.state.value}"})
        elif lc.state == LifecycleState.DEGRADED:
            checks.append({"name": "lifecycle", "status": "WARN", "detail": "System is degraded"})
            warning_count += 1
        else:
            checks.append({"name": "lifecycle", "status": "FAIL", "detail": f"System state {lc.state.value} cannot accept traffic"})
            critical_count += 1

        # 2. Health Engine
        health_res = self._health.check_health()
        if health_res.status == HealthStatus.HEALTHY:
            checks.append({"name": "subsystem_health", "status": "PASS", "detail": "All subsystems healthy"})
        elif health_res.status == HealthStatus.DEGRADED:
            checks.append({"name": "subsystem_health", "status": "WARN", "detail": "Subsystems degraded"})
            warning_count += 1
        else:
            checks.append({"name": "subsystem_health", "status": "FAIL", "detail": "Subsystems unhealthy"})
            critical_count += 1

        # 3. Store Integrity
        store_records = self._integrity.check_all_stores()
        corrupted = [s.store_name for s in store_records if s.corrupted]
        if corrupted:
            checks.append({"name": "store_integrity", "status": "FAIL", "detail": f"Corrupted stores: {len(corrupted)}"})
            critical_count += 1
        else:
            checks.append({"name": "store_integrity", "status": "PASS", "detail": f"{len(store_records)} stores verified"})

        # 4. Configuration Validity
        config_res = self._config.validate()
        if config_res.is_valid:
            checks.append({"name": "configuration", "status": "PASS", "detail": "Config valid"})
        else:
            checks.append({"name": "configuration", "status": "FAIL", "detail": f"Config errors: {config_res.errors}"})
            critical_count += 1

        # 5. Fail-closed decision logic
        if critical_count > 0:
            decision = ReadinessDecision.BLOCKED
            score = max(0.0, 10.0 - (critical_count * 3.0) - (warning_count * 1.0))
        elif warning_count > 0:
            decision = ReadinessDecision.NOT_READY
            score = max(0.0, 10.0 - (warning_count * 1.0))
        else:
            decision = ReadinessDecision.READY
            score = 10.0

        return ReadinessEvaluation(
            decision=decision,
            score=round(score, 1),
            checks=checks,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
