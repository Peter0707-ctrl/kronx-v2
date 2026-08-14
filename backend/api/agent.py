"""
Phase 2I — Agent API Router
Provides REST endpoints for submitting reasoning requests, monitoring status, querying traces, and cancelling jobs.
Guarantees authentication, tenant isolation, and error sanitization.
"""
from __future__ import annotations
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status

from agent.schemas import AgentRequest, AgentResult, AgentStatus
from agent.errors import (
    AgentError,
    AUTH_REQUIRED,
    SESSION_EXPIRED,
    SESSION_REVOKED,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    INTENT_UNCERTAIN,
    PERMISSION_REQUIRED,
    FORBIDDEN_PERMISSION_LEVEL,
    AGENT_NOT_FOUND,
)
from agent.orchestrator import AgentOrchestrator
from api.auth import get_auth_context
from auth.schemas import AuthenticationContext
from utils.logger import logger

agent_router = APIRouter(prefix="/api/agent", tags=["agent"])
_orchestrator = AgentOrchestrator()


def _handle_agent_error(e: AgentError):
    if e.code in (AUTH_REQUIRED, SESSION_EXPIRED, SESSION_REVOKED):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code in (WORKSPACE_NOT_AUTHORIZED, TENANT_NOT_AUTHORIZED, FORBIDDEN_PERMISSION_LEVEL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code == AGENT_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code == PERMISSION_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.detail}
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": e.code, "message": e.detail}
    )


@agent_router.post("/request", response_model=AgentResult)
def submit_agent_request(
    body: AgentRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Submits a user request to the AI Agent Brain."""
    try:
        return _orchestrator.run_agent_job(
            auth_context=context,
            request=body,
        )
    except AgentError as e:
        _handle_agent_error(e)


@agent_router.get("/{agent_id}", response_model=AgentResult)
def get_agent(
    agent_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Retrieves an agent job result by ID."""
    try:
        return _orchestrator.get_agent_result(context.tenant_id, agent_id)
    except AgentError as e:
        _handle_agent_error(e)


@agent_router.get("/{agent_id}/status", response_model=Dict[str, Any])
def get_agent_status(
    agent_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Returns the current execution status of an agent job."""
    try:
        res = _orchestrator.get_agent_result(context.tenant_id, agent_id)
        return {
            "status": "ok",
            "agent_id": res.agent_id,
            "agent_status": res.status,
            "summary": res.summary,
            "blocked_actions": res.blocked_actions,
            "warnings": res.warnings,
        }
    except AgentError as e:
        _handle_agent_error(e)


@agent_router.get("/{agent_id}/trace", response_model=Dict[str, Any])
def get_agent_trace(
    agent_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Retrieves the decision traces for the authenticated tenant."""
    traces = _orchestrator.get_agent_traces(context.tenant_id)
    return {
        "status": "ok",
        "agent_id": agent_id,
        "traces": traces,
    }


@agent_router.post("/{agent_id}/cancel", response_model=AgentResult)
def cancel_agent(
    agent_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Cooperatively cancels a running agent job."""
    try:
        return _orchestrator.cancel_agent_job(context.tenant_id, agent_id)
    except AgentError as e:
        _handle_agent_error(e)


@agent_router.post("/{agent_id}/revalidate", response_model=AgentResult)
def revalidate_agent(
    agent_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Re-runs verification or state check for an agent job."""
    try:
        return _orchestrator.get_agent_result(context.tenant_id, agent_id)
    except AgentError as e:
        _handle_agent_error(e)
