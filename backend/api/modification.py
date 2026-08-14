"""
Phase 2E — Modification API Router
Exposes:
  POST  /api/modification/propose
  POST  /api/modification/{proposal_id}/preview
  POST  /api/modification/{proposal_id}/approve
  POST  /api/modification/{proposal_id}/apply
  GET   /api/modification/{modification_id}
  POST  /api/modification/{modification_id}/rollback
  GET   /api/modification/{proposal_id}/diff
"""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field

from modification.orchestrator import ModificationOrchestrator
from modification.schemas import (
    ModificationRequest, PatchPayload, FilePatch,
    ModificationMode,
)
from modification.stores import ModificationStore, ProposalStore
from modification.errors import (
    ModificationError,
    PROPOSAL_NOT_FOUND,
    MODIFICATION_NOT_FOUND,
    AUTHORIZATION_NOT_FOUND,
    AUTHORIZATION_EXPIRED,
    AUTHORIZATION_CONSUMED,
    WORKSPACE_NOT_AUTHORIZED,
    PATH_OUTSIDE_WORKSPACE,
    ABSOLUTE_PATH_REJECTED,
    SENSITIVE_FILE,
    BLOCKED_SENSITIVE_CONTENT,
    BINARY_FILE_BLOCKED,
    GENERATED_PATH_BLOCKED,
    FILE_STATE_CHANGED,
    FILE_ALREADY_EXISTS,
    FILE_NOT_FOUND,
    RESOURCE_LIMIT,
    BLOCKED_REQUIRES_PERMISSION,
    PERMISSION_DENIED,
    FORBIDDEN_PERMISSION_LEVEL,
    ROLLBACK_CONFLICT,
)

router = APIRouter()
_orchestrator = ModificationOrchestrator()
_mod_store = ModificationStore()
_prop_store = ProposalStore()


class ProposeRequestBody(BaseModel):
    workspace_id:      str
    plan_id:           Optional[str] = None
    execution_id:      Optional[str] = None
    task_id:           Optional[str] = None
    patch:             PatchPayload
    user_id:           Optional[str] = None
    session_id:        Optional[str] = None
    tenant_id:         Optional[str] = None


class ApproveRequestBody(BaseModel):
    user_id:    Optional[str] = None
    session_id: Optional[str] = None
    tenant_id:  Optional[str] = None


class ApplyRequestBody(BaseModel):
    authorization_id: str


@router.post("/modification/propose")
async def propose_modification(
    body: ProposeRequestBody,
    x_request_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:8]}"

    req = ModificationRequest(
        request_id=req_id,
        workspace_id=body.workspace_id,
        plan_id=body.plan_id,
        execution_id=body.execution_id,
        task_id=body.task_id,
        mode=ModificationMode.PROPOSE,
        patch=body.patch,
        user_id=body.user_id,
        session_id=body.session_id,
        tenant_id=body.tenant_id,
    )

    try:
        proposal = _orchestrator.propose(req)
        return {"success": True, "proposal": proposal.model_dump()}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="PROPOSAL_FAILED")


@router.post("/modification/{proposal_id}/preview")
async def preview_modification(proposal_id: str) -> Dict[str, Any]:
    try:
        proposal = _orchestrator.preview(proposal_id)
        return {"success": True, "proposal": proposal.model_dump()}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="PREVIEW_FAILED")


@router.post("/modification/{proposal_id}/approve")
async def approve_modification(
    proposal_id: str,
    body: Optional[ApproveRequestBody] = None,
) -> Dict[str, Any]:
    body = body or ApproveRequestBody()
    try:
        auth_record = _orchestrator.approve(
            proposal_id=proposal_id,
            user_id=body.user_id,
            session_id=body.session_id,
            tenant_id=body.tenant_id,
        )
        return {"success": True, "authorization": auth_record.model_dump()}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="APPROVAL_FAILED")


@router.post("/modification/{proposal_id}/apply")
async def apply_modification(
    proposal_id: str,
    body: ApplyRequestBody,
) -> Dict[str, Any]:
    try:
        result = _orchestrator.apply(
            proposal_id=proposal_id,
            authorization_id=body.authorization_id,
        )
        return {"success": True, "modification": result.model_dump()}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="APPLY_FAILED")


@router.get("/modification/{modification_id}")
async def get_modification(modification_id: str) -> Dict[str, Any]:
    data = _mod_store.get_item(modification_id)
    if not data:
        raise HTTPException(status_code=404, detail=MODIFICATION_NOT_FOUND)
    return {"success": True, "modification": data}


@router.post("/modification/{modification_id}/rollback")
async def rollback_modification(modification_id: str) -> Dict[str, Any]:
    try:
        result = _orchestrator.rollback(modification_id)
        return {"success": True, "modification": result.model_dump()}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="ROLLBACK_FAILED")


@router.get("/modification/{proposal_id}/diff")
async def get_modification_diff(proposal_id: str) -> Dict[str, Any]:
    try:
        diff_data = _orchestrator.get_diff(proposal_id)
        return {"success": True, "diff": diff_data}
    except ModificationError as me:
        status_code = _modification_error_to_status(me.code)
        raise HTTPException(status_code=status_code, detail=me.code)
    except Exception:
        raise HTTPException(status_code=500, detail="DIFF_FAILED")


def _modification_error_to_status(code: str) -> int:
    mapping = {
        WORKSPACE_NOT_AUTHORIZED:    403,
        PROPOSAL_NOT_FOUND:          404,
        MODIFICATION_NOT_FOUND:      404,
        AUTHORIZATION_NOT_FOUND:     404,
        AUTHORIZATION_EXPIRED:       403,
        AUTHORIZATION_CONSUMED:      403,
        PATH_OUTSIDE_WORKSPACE:      403,
        ABSOLUTE_PATH_REJECTED:      400,
        SENSITIVE_FILE:              403,
        BLOCKED_SENSITIVE_CONTENT:   422,
        BINARY_FILE_BLOCKED:         422,
        GENERATED_PATH_BLOCKED:      403,
        FILE_STATE_CHANGED:          409,
        FILE_ALREADY_EXISTS:         409,
        FILE_NOT_FOUND:              404,
        RESOURCE_LIMIT:              413,
        BLOCKED_REQUIRES_PERMISSION: 403,
        PERMISSION_DENIED:           403,
        FORBIDDEN_PERMISSION_LEVEL:  403,
        ROLLBACK_CONFLICT:           409,
    }
    return mapping.get(code, 422)
