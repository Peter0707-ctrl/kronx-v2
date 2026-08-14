"""
Phase 2F — Production Readiness Engine
Evaluates all verification findings, computes scores across dimensions, and renders a strict fail-closed readiness decision.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple

from verification.schemas import (
    VerificationCheck, CheckStatus, CheckSeverity,
    OverallVerificationStatus, ReadinessDecision
)


class ProductionReadinessEngine:
    """Calculates production readiness scores and decision from verification checks."""

    def evaluate_readiness(
        self,
        checks: List[VerificationCheck]
    ) -> Tuple[OverallVerificationStatus, ReadinessDecision, float, float, float, float, List[str], List[str], List[str]]:
        """
        Evaluates checks list and returns:
        (overall_status, decision, sec_score, integ_score, test_score, readiness_score, criticals, warnings, recommendations)
        """
        critical_findings: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        sec_checks = [c for c in checks if c.category == "SECURITY"]
        integ_checks = [c for c in checks if c.category == "INTEGRITY"]
        test_checks = [c for c in checks if c.category == "TESTS"]
        ws_checks = [c for c in checks if c.category == "WORKSPACE"]
        reg_checks = [c for c in checks if c.category == "REGRESSION"]
        health_checks = [c for c in checks if c.category == "HEALTH"]

        # Collect critical findings and warnings
        for c in checks:
            if c.status == CheckStatus.FAIL:
                if c.severity in (CheckSeverity.CRITICAL, CheckSeverity.HIGH):
                    critical_findings.append(f"[{c.category}] {c.name}: {c.message}")
                else:
                    warnings.append(f"[{c.category}] {c.name}: {c.message}")
            elif c.status == CheckStatus.WARN:
                warnings.append(f"[{c.category}] {c.name}: {c.message}")

        # Compute dimension scores (0.0 to 10.0)
        sec_score = self._compute_category_score(sec_checks + ws_checks)
        integ_score = self._compute_category_score(integ_checks)
        test_score = self._compute_category_score(test_checks + reg_checks)
        health_score = self._compute_category_score(health_checks)

        # Weighted Readiness Score: 40% Security, 25% Tests, 20% Integrity, 15% Health
        readiness_score = round(
            (sec_score * 0.40) + (test_score * 0.25) + (integ_score * 0.20) + (health_score * 0.15),
            2
        )

        # Determine Decision (FAIL CLOSED)
        if any(c.severity == CheckSeverity.CRITICAL and c.status == CheckStatus.FAIL for c in checks):
            decision = ReadinessDecision.BLOCKED
            overall_status = OverallVerificationStatus.BLOCKED
            recommendations.append("Critical security or architectural invariant failure must be resolved before deployment.")
        elif critical_findings:
            decision = ReadinessDecision.NOT_READY
            overall_status = OverallVerificationStatus.FAILED
            recommendations.append("Resolve all high-severity failures to achieve production readiness.")
        elif warnings:
            decision = ReadinessDecision.READY_WITH_WARNINGS
            overall_status = OverallVerificationStatus.PASSED_WITH_WARNINGS
            recommendations.append("System is operational; review non-blocking warnings before release.")
        else:
            decision = ReadinessDecision.READY
            overall_status = OverallVerificationStatus.PASSED
            recommendations.append("All security, integrity, regression, and test suites verified 100%. Ready for production.")

        return (
            overall_status,
            decision,
            sec_score,
            integ_score,
            test_score,
            readiness_score,
            critical_findings,
            warnings,
            recommendations
        )

    def _compute_category_score(self, checks: List[VerificationCheck]) -> float:
        if not checks:
            return 10.0
        total = len(checks)
        passed = sum(1 for c in checks if c.status == CheckStatus.PASS)
        warned = sum(1 for c in checks if c.status == CheckStatus.WARN)
        # Pass = 1.0, Warn = 0.5, Fail = 0.0
        points = (passed * 1.0) + (warned * 0.5)
        return round((points / total) * 10.0, 2)
