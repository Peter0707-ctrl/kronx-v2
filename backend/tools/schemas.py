from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ToolExecutionContext(BaseModel):
    request_id: str
    workspace_id: str
    tool_call_id: str
    effective_permission: str  # READ, WRITE, EXECUTE, NETWORK, ADMIN
    canonical_workspace_root: str

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    success: bool
    tool: str
    tool_call_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
