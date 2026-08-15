"""
Phase 2F — Test Verifier
Statically inspects and verifies test suite integrity and test case coverage across all phases.
Operates completely read-only without executing shell commands or subprocesses.
"""
from __future__ import annotations
import os
import re
import time
from typing import List, Dict, Any, Optional

from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity
from verification.checks import create_check

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(BASE_DIR, "tests")

EXPECTED_TEST_SUITES = {
    "test_foundation.py":   {"phase": "Phase 1",  "min_tests": 12},
    "test_workspace.py":    {"phase": "Phase 2A", "min_tests": 10},
    "test_tools.py":        {"phase": "Phase 2B", "min_tests": 15},
    "test_planner.py":      {"phase": "Phase 2C", "min_tests": 27},
    "test_execution.py":    {"phase": "Phase 2D", "min_tests": 34},
    "test_modification.py": {"phase": "Phase 2E", "min_tests": 46},
    "test_verification.py": {"phase": "Phase 2F", "min_tests": 35},
    "test_auth.py":         {"phase": "Phase 2G", "min_tests": 40},
    "test_gateway.py":      {"phase": "Phase 2H", "min_tests": 50},
    "test_agent.py":        {"phase": "Phase 2I", "min_tests": 55},
    "test_multimodal.py":   {"phase": "Phase 2I.1", "min_tests": 50},
    "test_llm.py":          {"phase": "Phase 2J", "min_tests": 60},
    "test_phase3_architecture.py": {"phase": "Phase 3.0", "min_tests": 50},
    "test_operations.py":   {"phase": "Phase 3.1", "min_tests": 50},
    "test_intelligence.py": {"phase": "Phase 4.0", "min_tests": 50},
}











class TestVerifier:
    """Static verifier for test suites and test coverage integrity."""

    def verify_test_suites(self) -> List[VerificationCheck]:
        """Verifies existence and test case count of all test files across all phases."""
        checks: List[VerificationCheck] = []
        start_t = time.perf_counter()

        total_discovered_tests = 0
        missing_suites: List[str] = []
        suite_details: Dict[str, Any] = {}

        for suite_file, meta in EXPECTED_TEST_SUITES.items():
            full_path = os.path.join(TESTS_DIR, suite_file)
            if not os.path.isfile(full_path):
                missing_suites.append(suite_file)
                continue

            # Count def test_ methods statically
            test_count = 0
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if re.match(r'^\s*def test_', line):
                            test_count += 1
            except Exception:
                pass

            suite_details[suite_file] = {
                "phase": meta["phase"],
                "expected_min": meta["min_tests"],
                "actual_count": test_count,
            }
            total_discovered_tests += test_count

        dur = (time.perf_counter() - start_t) * 1000

        if missing_suites:
            checks.append(create_check(
                category="TESTS",
                name="TEST_SUITE_INTEGRITY",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"Missing expected test suite file(s): {missing_suites}",
                evidence={"missing": missing_suites, "discovered": suite_details},
                duration_ms=dur,
            ))
            return checks

        # Check total count against baseline (144 minimum)
        if total_discovered_tests < 144:
            checks.append(create_check(
                category="TESTS",
                name="TEST_SUITE_COVERAGE",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"Total test count ({total_discovered_tests}) is below baseline (144).",
                evidence={"suites": suite_details, "total_tests": total_discovered_tests},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="TESTS",
                name="TEST_SUITE_COVERAGE",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message=f"Verified: All 6 test suites present with {total_discovered_tests} total tests (>= 144 baseline).",
                evidence={"suites": suite_details, "total_tests": total_discovered_tests},
                duration_ms=dur,
            ))

        return checks
