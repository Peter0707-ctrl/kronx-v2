"""
Phase 2C — Planner API Router
Exposes:
  POST   /api/planner/plan
  GET    /api/planner/plan/{plan_id}
  POST   /api/planner/plan/{plan_id}/validate
  GET    /api/planner/plan/{plan_id}/status
"""
from __future__ import annotations
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field, field_validator

from planner.planner import KronxPlanner, PlannerError
from planner.validator import PlanValidator, PlanValidationError
from planner.store import PlannerStore
from planner.schemas import PlanningMode, PlanningResult, MAX_OBJECTIVE_LENGTH

router = APIRouter()
_planner = KronxPlanner()
_store   = PlannerStore()
_validator = PlanValidator()


# ------------------------------------------------------------------
# Request body
# ------------------------------------------------------------------

class PlanRequest(BaseModel):
    workspace_id:    str
    objective:       str = Field(..., min_length=1)
    constraints:     list = Field(default_factory=list)
    requested_mode:  str  = "ANALYZE"
    language:        str  = "auto"
    conversation_id: Optional[str] = None

    @field_validator("objective")
    @classmethod
    def cap_objective(cls, v: str) -> str:
        if len(v) > MAX_OBJECTIVE_LENGTH:
            raise ValueError(f"Objective exceeds {MAX_OBJECTIVE_LENGTH} characters.")
        return v


# ------------------------------------------------------------------
# POST /api/planner/plan
# ------------------------------------------------------------------

@router.post("/planner/plan")
async def create_plan(
    body: PlanRequest,
    x_request_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:8]}"

    # Validate mode
    try:
        mode = PlanningMode(body.requested_mode.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid planning mode: '{body.requested_mode}'.")

    from planner.schemas import PlanningRequest
    req = PlanningRequest(
        request_id=req_id,
        workspace_id=body.workspace_id,
        objective=body.objective,
        constraints=body.constraints,
        requested_mode=mode,
        language=body.language,
        conversation_id=body.conversation_id,
    )

    try:
        result = _planner.plan(req)
    except PlannerError as pe:
        _http_code = _planner_error_to_status(pe.code)
        raise HTTPException(status_code=_http_code, detail=pe.code)
    except Exception:
        raise HTTPException(status_code=500, detail="PLANNING_FAILED")

    return {"success": True, "plan": result.model_dump()}


# ------------------------------------------------------------------
# GET /api/planner/plan/{plan_id}
# ------------------------------------------------------------------

@router.get("/planner/plan/{plan_id}")
async def get_plan(plan_id: str) -> Dict[str, Any]:
    plan_data = _store.get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="PLAN_NOT_FOUND")
    return {"success": True, "plan": plan_data}


# ------------------------------------------------------------------
# POST /api/planner/plan/{plan_id}/validate
# ------------------------------------------------------------------

@router.post("/planner/plan/{plan_id}/validate")
async def validate_plan(plan_id: str) -> Dict[str, Any]:
    plan_data = _store.get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="PLAN_NOT_FOUND")
    try:
        result = PlanningResult(**plan_data)
        _validator.validate(result)
        return {"success": True, "plan_id": plan_id, "valid": True}
    except PlanValidationError as ve:
        raise HTTPException(status_code=422, detail=ve.code)
    except Exception:
        raise HTTPException(status_code=500, detail="VALIDATION_FAILED")


# ------------------------------------------------------------------
# GET /api/planner/plan/{plan_id}/status
# ------------------------------------------------------------------

@router.get("/planner/plan/{plan_id}/status")
async def plan_status(plan_id: str) -> Dict[str, Any]:
    plan_data = _store.get_plan(plan_id)
    if not plan_data:
        raise HTTPException(status_code=404, detail="PLAN_NOT_FOUND")
    return {
        "plan_id":    plan_id,
        "status":     plan_data.get("status", "UNKNOWN"),
        "created_at": plan_data.get("created_at"),
        "mode":       plan_data.get("mode"),
        "task_count": len(plan_data.get("tasks", [])),
    }


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def _planner_error_to_status(code: str) -> int:
    mapping = {
        "WORKSPACE_NOT_AUTHORIZED": 403,
        "EMPTY_OBJECTIVE":          400,
        "CIRCULAR_DEPENDENCY":      422,
        "DUPLICATE_TASK_ID":        422,
        "MISSING_DEPENDENCY":       422,
        "RESOURCE_LIMIT":           413,
        "PLAN_TOO_LARGE":           413,
        "SENSITIVE_CONTENT_DETECTED": 422,
    }
    return mapping.get(code, 500)
