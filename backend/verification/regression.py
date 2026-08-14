"""
Phase 2F — Regression Detector
Compares current API routes, module exports, and security gates against the verified baseline to prevent silent regressions.
"""
from __future__ import annotations
import time
from typing import List, Dict, Any, Set

from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity
from verification.checks import create_check

EXPECTED_ROUTERS = [
    "/api/chat",
    "/api/memories",
    "/api/workspace",
    "/api/tools",
    "/api/planner",
    "/api/execution",
    "/api/modification",
    "/api/verification",
    "/api/auth",
    "/api/health",
    "/api/agent",
    "/api/multimodal",
    "/api/llm",
]


EXPECTED_MODULES = [
    "orchestrator.core",
    "memory.store",
    "workspace.manager",
    "workspace.store",
    "tools.runtime",
    "tools.permissions",
    "planner.planner",
    "execution.orchestrator",
    "modification.orchestrator",
    "verification.orchestrator",
    "auth.store",
    "auth.authentication",
    "auth.authorization",
    "gateway.gateway",
    "gateway.rate_limit",
    "gateway.quotas",
    "agent.agent",
    "agent.intent",
    "agent.policy",
    "agent.orchestrator",
    "multimodal.orchestrator",
    "multimodal.policy",
    "multimodal.file_analyzer",
    "llm.orchestrator",
    "llm.policy",
    "llm.router",
]







class RegressionDetector:
    """Detects regressions across API endpoints, routers, and core architectural components."""

    def detect_regressions(self) -> List[VerificationCheck]:
        """Runs full regression detection suite."""
        checks: List[VerificationCheck] = []
        
        # 1. Router & API Endpoint Regression Check
        start_t = time.perf_counter()
        from main import app
        
        registered_paths: Set[str] = set()
        for r in app.routes:
            p = getattr(r, "path", None)
            if p:
                registered_paths.add(p)
            if hasattr(r, "include_context") and hasattr(r, "original_router"):
                pfx = getattr(r.include_context, "prefix", "") or ""
                for sr in getattr(r.original_router, "routes", []):
                    sub_p = getattr(sr, "path", "")
                    registered_paths.add(f"{pfx}{sub_p}")

        missing_prefixes: List[str] = []




        for expected_prefix in EXPECTED_ROUTERS:
            # Check if any route starts with expected_prefix
            matched = any(p.startswith(expected_prefix) for p in registered_paths)
            if not matched:
                missing_prefixes.append(expected_prefix)

        dur = (time.perf_counter() - start_t) * 1000

        if missing_prefixes:
            checks.append(create_check(
                category="REGRESSION",
                name="API_ROUTER_REGRESSION",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"Missing expected API router prefix(es): {missing_prefixes}",
                evidence={"missing": missing_prefixes, "total_routes": len(registered_paths)},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="REGRESSION",
                name="API_ROUTER_REGRESSION",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message=f"Verified: All {len(EXPECTED_ROUTERS)} core API routers registered ({len(registered_paths)} total routes).",
                evidence={"registered_prefixes": EXPECTED_ROUTERS, "total_routes": len(registered_paths)},
                duration_ms=dur,
            ))

        # 2. Module Import Regression Check
        start_t = time.perf_counter()
        failed_imports: List[str] = []

        for mod_name in EXPECTED_MODULES:
            try:
                __import__(mod_name)
            except Exception as e:
                failed_imports.append(f"{mod_name}: {e}")

        dur = (time.perf_counter() - start_t) * 1000

        if failed_imports:
            checks.append(create_check(
                category="REGRESSION",
                name="CORE_MODULE_REGRESSION",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"Core module import regression detected: {failed_imports}",
                evidence={"failed_imports": failed_imports},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="REGRESSION",
                name="CORE_MODULE_REGRESSION",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message=f"Verified: All {len(EXPECTED_MODULES)} foundational modules load without error.",
                evidence={"modules_checked": EXPECTED_MODULES},
                duration_ms=dur,
            ))

        return checks
