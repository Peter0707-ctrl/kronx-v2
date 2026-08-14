"""
Phase 2F — Verification API Endpoints
Exposes structured verification, health status, and production readiness checks.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from verification.orchestrator import VerificationOrchestrator
from verification.schemas import (
    VerificationRequest, VerificationResult, VerificationType
)
from verification.errors import (
    VerificationError,
    WORKSPACE_NOT_AUTHORIZED,
    VERIFICATION_NOT_FOUND,
)
from utils.logger import logger

verification_router = APIRouter(prefix="/api/verification", tags=["verification"])
_orchestrator = VerificationOrchestrator()


class RunVerificationPayload(BaseModel):
    workspace_id:             str
    verification_type:        VerificationType = VerificationType.FULL
    plan_id:                  Optional[str] = None
    execution_id:             Optional[str] = None
    modification_id:          Optional[str] = None
    include_tests:            bool = True
    include_security_checks:   bool = True
    include_integrity_checks:  bool = True
    include_health_checks:     bool = True


def _handle_error(e: VerificationError):
    if e.code == WORKSPACE_NOT_AUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code == VERIFICATION_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.detail}
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": e.code, "message": e.detail}
    )


@verification_router.post("/run", response_model=Dict[str, Any])
def run_verification(payload: RunVerificationPayload):
    """Executes verification and returns comprehensive readiness results."""
    req = VerificationRequest(
        request_id=f"req_ver_{payload.workspace_id[:8]}",
        workspace_id=payload.workspace_id,
        verification_type=payload.verification_type,
        plan_id=payload.plan_id,
        execution_id=payload.execution_id,
        modification_id=payload.modification_id,
        include_tests=payload.include_tests,
        include_security_checks=payload.include_security_checks,
        include_integrity_checks=payload.include_integrity_checks,
        include_health_checks=payload.include_health_checks,
    )
    try:
        res = _orchestrator.run_verification(req)
        return {"status": "ok", "verification": res.model_dump()}
    except VerificationError as e:
        _handle_error(e)


@verification_router.get("/{verification_id}", response_model=Dict[str, Any])
def get_verification(verification_id: str):
    """Retrieves full verification result by ID."""
    res = _orchestrator.get_verification(verification_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": VERIFICATION_NOT_FOUND, "message": f"Verification '{verification_id}' not found."}
        )
    return {"status": "ok", "verification": res.model_dump()}


@verification_router.get("/{verification_id}/status", response_model=Dict[str, Any])
def get_verification_status(verification_id: str):
    """Retrieves status and decision summary for a verification."""
    res = _orchestrator.get_verification(verification_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": VERIFICATION_NOT_FOUND, "message": f"Verification '{verification_id}' not found."}
        )
    return {
        "status": "ok",
        "verification_id": res.verification_id,
        "verification_status": res.status,
        "readiness_decision": res.readiness_decision,
        "readiness_score": res.readiness_score,
        "security_score": res.security_score,
        "critical_findings_count": len(res.critical_findings),
        "warnings_count": len(res.warnings),
    }


@verification_router.get("/{verification_id}/checks", response_model=Dict[str, Any])
def get_verification_checks(verification_id: str):
    """Retrieves individual verification check records."""
    res = _orchestrator.get_verification(verification_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": VERIFICATION_NOT_FOUND, "message": f"Verification '{verification_id}' not found."}
        )
    return {
        "status": "ok",
        "verification_id": res.verification_id,
        "check_count": len(res.checks),
        "checks": [c.model_dump() for c in res.checks],
    }


@verification_router.post("/{verification_id}/revalidate", response_model=Dict[str, Any])
def revalidate_verification(verification_id: str):
    """Re-runs verification against current state for the same workspace."""
    res = _orchestrator.get_verification(verification_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": VERIFICATION_NOT_FOUND, "message": f"Verification '{verification_id}' not found."}
        )
    req = VerificationRequest(
        request_id=f"reval_{verification_id[:8]}",
        workspace_id=res.workspace_id,
    )
    try:
        new_res = _orchestrator.run_verification(req)
        return {"status": "ok", "verification": new_res.model_dump()}
    except VerificationError as e:
        _handle_error(e)
