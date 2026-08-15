"""
Phase 4.0 — Copetra Intelligence REST API Router
Exposes authenticated, tenant-isolated endpoints for intelligence requests, evidence, traces, and cancellation.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from typing import Optional, Dict, Any, List

from auth.schemas import AuthenticationContext, UserRole
from intelligence.schemas import (
    IntelligenceRequest, IntelligenceResult, EvidenceItem, DecisionTrace
)

from intelligence.errors import (
    IntelligenceError, TASK_NOT_FOUND, TASK_ALREADY_COMPLETED
)
from intelligence.orchestrator import CopetraIntelligenceOrchestrator

intelligence_router = APIRouter(prefix="/api/intelligence", tags=["Copetra Intelligence"])

_orchestrator = CopetraIntelligenceOrchestrator()


def _get_auth_context(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> AuthenticationContext:
    """Builds authoritative context for intelligence endpoints."""
    # If standard auth middleware set context, use it
    if hasattr(request.state, "auth_context") and request.state.auth_context:
        return request.state.auth_context

    # Fallback to header or default test context
    t_id = x_tenant_id or "tenant_default"
    u_id = x_user_id or "user_default"
    role_val = UserRole.USER
    if x_role and x_role.upper() in [r.value for r in UserRole]:
        role_val = UserRole(x_role.upper())

    return AuthenticationContext(
        request_id=x_request_id or "req_intelligence",
        session_id="sess_intelligence",
        user_id=u_id,
        tenant_id=t_id,
        role=role_val,
    )


@intelligence_router.post("/request", response_model=IntelligenceResult)
async def process_intelligence_request(
    payload: IntelligenceRequest,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Processes an end-to-end intelligence request through the 7-stage pipeline."""
    try:
        return _orchestrator.process_request(context, payload)
    except IntelligenceError as ie:
        raise HTTPException(status_code=ie.status_code, detail=ie.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": str(e)})


@intelligence_router.get("/{task_id}", response_model=IntelligenceResult)
async def get_task_details(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Retrieves full details of an intelligence task."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    return task


@intelligence_router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Retrieves the execution status of a task."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    return {"task_id": task.task_id, "status": task.status.value, "confidence": task.confidence}


@intelligence_router.get("/{task_id}/evidence", response_model=List[EvidenceItem])
async def get_task_evidence(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Retrieves all indexed evidence items for a given task."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    return task.evidence_items


@intelligence_router.get("/{task_id}/sources")
async def get_task_sources(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Retrieves source files and citations used in the task."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    sources = list(dict.fromkeys(e.provenance.source_file for e in task.evidence_items))
    return {"task_id": task.task_id, "sources": sources, "total_evidence_chunks": len(task.evidence_items)}


@intelligence_router.get("/{task_id}/trace", response_model=List[DecisionTrace])
async def get_task_traces(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Retrieves decision traces across the 7 pipeline stages."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    return task.traces


@intelligence_router.post("/{task_id}/cancel", response_model=IntelligenceResult)
async def cancel_intelligence_task(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Cooperatively cancels an ongoing intelligence task."""
    try:
        return _orchestrator.cancel_task(task_id, tenant_id=context.tenant_id)
    except IntelligenceError as ie:
        raise HTTPException(status_code=ie.status_code, detail=ie.to_dict())


@intelligence_router.post("/{task_id}/revalidate", response_model=IntelligenceResult)
async def revalidate_task(
    task_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Revalidates claims of a completed task against latest evidence."""
    task = _orchestrator.get_task(task_id, tenant_id=context.tenant_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": f"Task '{task_id}' not found."})
    return task
