from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from tools.runtime import ToolRuntime
from tools.schemas import ToolResult
from tools.errors import (
    WORKSPACE_NOT_AUTHORIZED, PATH_OUTSIDE_WORKSPACE, 
    TOOL_NOT_REGISTERED, PERMISSION_DENIED, SENSITIVE_FILE, 
    RESOURCE_LIMIT, INVALID_ARGUMENTS, TOOL_EXECUTION_FAILED
)

router = APIRouter()
runtime = ToolRuntime()

class ToolExecuteRequest(BaseModel):
    workspace_id: str
    tool_name: str
    arguments: Dict[str, Any]
    effective_permission: Optional[str] = "READ"

@router.post("/tools/execute", response_model=ToolResult)
async def execute_tool(
    payload: ToolExecuteRequest,
    x_request_id: Optional[str] = Header(None)
):
    """
    Executes a registered tool within the safe ToolRuntime boundary.
    Exposes safe HTTP exception mappings.
    """
    req_id = x_request_id or f"req_{uuid.uuid4().hex[:8]}"
    
    res = runtime.execute_tool(
        request_id=req_id,
        workspace_id=payload.workspace_id,
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        client_effective_permission=payload.effective_permission
    )
    
    if not res.success:
        # Standardized safe errors: map to correct status codes
        if res.error in [WORKSPACE_NOT_AUTHORIZED, PATH_OUTSIDE_WORKSPACE, PERMISSION_DENIED, SENSITIVE_FILE]:
            raise HTTPException(status_code=403, detail=res.error)
        elif res.error == TOOL_NOT_REGISTERED:
            raise HTTPException(status_code=404, detail=res.error)
        elif res.error == INVALID_ARGUMENTS:
            raise HTTPException(status_code=400, detail=res.error)
        else:
            raise HTTPException(status_code=500, detail=TOOL_EXECUTION_FAILED)
            
    return res
