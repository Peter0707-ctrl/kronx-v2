"""
Phase 2H — Health & Readiness Checks
Verifies core subsystems, persistence stores, and runtime availability without exposing system internals.
"""
from __future__ import annotations
import os
import time
from fastapi import APIRouter, Response, status

from config.settings import config
from gateway.schemas import HealthState, HealthCheckResponse
from utils.logger import logger

health_router = APIRouter(prefix="/api/health", tags=["health"])
_start_time = time.time()


def perform_health_check() -> HealthCheckResponse:
    """Evaluates the readiness and availability of all core storage systems."""
    now = time.time()
    uptime = now - _start_time
    components = {}
    is_ready = True
    is_live = True

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    critical_stores = [
        ("auth_store", "auth_store.json"),
        ("workspace_store", "workspace_store.json"),
        ("planner_store", "planner_store.json"),
        ("execution_store", "execution_store.json"),
        ("modification_store", "modification_store.json"),
        ("verification_store", "verification_store.json"),
    ]

    for label, fname in critical_stores:
        fpath = os.path.join(base_dir, fname)
        try:
            if not os.path.exists(fpath):
                # Ensure creatable/writable
                with open(fpath, "a", encoding="utf-8") as _:
                    pass
            # Check read access
            with open(fpath, "r", encoding="utf-8") as _:
                pass
            components[label] = "HEALTHY"
        except Exception as e:
            logger.error(f"[health] Store check failed for {label}: {e}")
            components[label] = "UNAVAILABLE"
            is_ready = False

    state = HealthState.READY if is_ready else HealthState.DEGRADED

    return HealthCheckResponse(
        status=state,
        version="2.0.0",
        environment=config.environment,
        uptime_sec=round(uptime, 2),
        components=components,
    )


@health_router.get("", response_model=HealthCheckResponse)
def get_health(response: Response):
    check = perform_health_check()
    if check.status == HealthState.BLOCKED:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return check


@health_router.get("/live")
def get_liveness():
    return {"status": "LIVE"}


@health_router.get("/ready")
def get_readiness(response: Response):
    check = perform_health_check()
    if check.status != HealthState.READY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "NOT_READY", "details": check.components}
    return {"status": "READY"}
