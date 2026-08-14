"""
Phase 2D — Execution API Router
Exposes:
  POST  /api/execution/start
  GET   /api/execution/{execution_id}
  POST  /api/execution/{execution_id}/cancel
  GET   /api/execution/{execution_id}/tasks
  POST  /api/execution/{execution_id}/pause
  POST  /api/execution/{execution_id}/resume
"""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from execution.orchestrator import ExecutionOrchestrator
from execution.schemas import ExecutionRequest, ExecutionMode, ExecutionResult
from execution.checkpoint import ExecutionStore
from execution.errors import (
    ExecutionError, EXECUTION_NOT_FOUND, PLAN_NOT_FOUND,
    WORKSPACE_NOT_AUTHORIZED, INVALID_TASK_ID,
    BLOCKED_REQUIRES_PERMISSION, FORBIDDEN_PERMISSION_LEVEL,
    RESOURCE_LIMIT_EXCEEDED,
)

router = APIRouter()
_orchestrator = ExecutionOrchestrator()
_store = ExecutionStore()


class StartExecutionBody(BaseModel):
    workspace_id:       str
    plan_id:            str
    confirmation_token: Optional[str] = None
    requested_task_ids: Optional[List[str]] = None
    execution_mode:     str = "DRY_RUN"
    user_id:            Optional[str] = None
    session_id:         Optional[str] = None
    tenant_id:          Optional[str] = None


@router.post("/execution/start")
async def start_execution(
    body: StartExecutionBody,
    x_request_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:8]}"

    try:
        mode = ExecutionMode(body.execution_mode.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid execution mode: '{body.execution_mode}'.")

    req = ExecutionRequest(
        request_id=req_id,
        workspace_id=body.workspace_id,
        plan_id=body.plan_id,
        confirmation_token=body.confirmation_token,
        requested_task_ids=body.requested_task_ids,
        execution_mode=mode,
        user_id=body.user_id,
        session_id=body.session_id,
        tenant_id=body.tenant_id,
    )

    try:
        result = _orchestrator.execute(req)
        return {"success": True, "execution": result.model_dump()}
    except ExecutionError as ee:
        status_code = _execution_error_to_status(ee.code)
        raise HTTPException(status_code=status_code, detail=ee.code)
    except Exception:
        raise HTTPException(status_code=500, detail="EXECUTION_FAILED")


@router.get("/execution/{execution_id}")
async def get_execution(execution_id: str) -> Dict[str, Any]:
    exec_data = _store.get_execution(execution_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail=EXECUTION_NOT_FOUND)
    return {"success": True, "execution": exec_data}


@router.post("/execution/{execution_id}/cancel")
async def cancel_execution(execution_id: str) -> Dict[str, Any]:
    try:
        result = _orchestrator.cancel(execution_id)
        return {"success": True, "execution": result.model_dump()}
    except ExecutionError as ee:
        status_code = _execution_error_to_status(ee.code)
        raise HTTPException(status_code=status_code, detail=ee.code)
    except Exception:
        raise HTTPException(status_code=500, detail="CANCEL_FAILED")


@router.get("/execution/{execution_id}/tasks")
async def get_execution_tasks(execution_id: str) -> Dict[str, Any]:
    exec_data = _store.get_execution(execution_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail=EXECUTION_NOT_FOUND)
    return {
        "success": True,
        "execution_id": execution_id,
        "status": exec_data.get("status"),
        "tasks": exec_data.get("tasks", []),
    }


@router.post("/execution/{execution_id}/pause")
async def pause_execution(execution_id: str) -> Dict[str, Any]:
    try:
        result = _orchestrator.pause(execution_id)
        return {"success": True, "execution": result.model_dump()}
    except ExecutionError as ee:
        status_code = _execution_error_to_status(ee.code)
        raise HTTPException(status_code=status_code, detail=ee.code)
    except Exception:
        raise HTTPException(status_code=500, detail="PAUSE_FAILED")


@router.post("/execution/{execution_id}/resume")
async def resume_execution(execution_id: str) -> Dict[str, Any]:
    try:
        result = _orchestrator.resume(execution_id)
        return {"success": True, "execution": result.model_dump()}
    except ExecutionError as ee:
        status_code = _execution_error_to_status(ee.code)
        raise HTTPException(status_code=status_code, detail=ee.code)
    except Exception:
        raise HTTPException(status_code=500, detail="RESUME_FAILED")


def _execution_error_to_status(code: str) -> int:
    mapping = {
        WORKSPACE_NOT_AUTHORIZED:    403,
        PLAN_NOT_FOUND:              404,
        EXECUTION_NOT_FOUND:         404,
        INVALID_TASK_ID:             400,
        BLOCKED_REQUIRES_PERMISSION: 403,
        FORBIDDEN_PERMISSION_LEVEL:  403,
        RESOURCE_LIMIT_EXCEEDED:     413,
    }
    return mapping.get(code, 422)
