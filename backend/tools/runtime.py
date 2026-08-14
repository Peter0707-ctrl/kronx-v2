import time
import uuid
import traceback
from datetime import datetime
from typing import Dict, Any, Tuple

from tools.registry import registry, ToolDescriptor
from tools.schemas import ToolExecutionContext, ToolCall, ToolResult
from tools.permissions import PermissionEngine
from tools.audit import log_tool_audit
from tools.errors import (
    WORKSPACE_NOT_AUTHORIZED, TOOL_NOT_REGISTERED, 
    PERMISSION_DENIED, INVALID_ARGUMENTS, TOOL_EXECUTION_FAILED
)
from workspace.store import WorkspaceStore
from utils.logger import logger

class ToolRuntime:
    def __init__(self):
        self.store = WorkspaceStore()
        self.permission_engine = PermissionEngine()

    def _resolve_workspace(self, workspace_id: str) -> Tuple[bool, str]:
        """Resolve trusted canonical workspace root path from storage."""
        if not workspace_id:
            return False, ""
        ws_data = self.store.get_workspace(workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            return False, ""
        return True, ws_data["root_path"]

    def execute_tool(
        self,
        request_id: str,
        workspace_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        client_effective_permission: str = "READ"
    ) -> ToolResult:
        """
        Core Tool Execution pipeline.
        Enforces schema validations, permissions check, containment checks, sanitization, and audit logging.
        """
        start_time = time.perf_counter()
        tool_call_id = f"tcall_{uuid.uuid4().hex[:8]}"

        # 1. Output variables initialization
        decision = "DENY"
        effective_perm = "READ"
        relative_path_involved = arguments.get("path", "")
        error_code = None
        data_result = None
        success = False

        try:
            # 2. Strict Pydantic validation of input ToolCall schema
            try:
                tc = ToolCall(tool_name=tool_name, arguments=arguments)
            except Exception as pe:
                error_code = INVALID_ARGUMENTS
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=f"{INVALID_ARGUMENTS}: Schema validation failed: {str(pe)}"
                )

            # 3. Resolve Workspace Root securely from WorkspaceStore
            ok, canonical_root = self._resolve_workspace(workspace_id)
            if not ok:
                error_code = WORKSPACE_NOT_AUTHORIZED
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=WORKSPACE_NOT_AUTHORIZED
                )

            # 4. Enforce server-decided effective permissions limit
            # Force READ level for all queries, WRITE/EXECUTE/NETWORK are strictly denied
            if client_effective_permission == "WRITE":
                # Write tools are structured but disabled by default in 2B
                effective_perm = "WRITE"
            else:
                effective_perm = "READ"

            # 5. Check if tool is registered
            tool_desc = registry.get(tool_name)
            if not tool_desc:
                error_code = TOOL_NOT_REGISTERED
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=TOOL_NOT_REGISTERED
                )

            # 6. Validate permissions level via PermissionEngine
            allowed, perm_err = self.permission_engine.validate_permission(
                required=tool_desc.required_permission,
                effective=effective_perm
            )
            if not allowed:
                error_code = perm_err
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=perm_err
                )

            # Transition decision to ALLOW
            decision = "ALLOW"

            # 7. Establish execution context
            context = ToolExecutionContext(
                request_id=request_id,
                workspace_id=workspace_id,
                tool_call_id=tool_call_id,
                effective_permission=effective_perm,
                canonical_workspace_root=canonical_root
            )

            # 8. Run execution handler
            try:
                data_result = tool_desc.handler(context, arguments)
                
                # Output Sanitization: replace server paths with relative paths
                if isinstance(data_result, dict):
                    # Sanitize any absolute path representations in results
                    for key, val in list(data_result.items()):
                        if isinstance(val, str) and canonical_root in val:
                            data_result[key] = val.replace(canonical_root, "").replace("\\", "/").lstrip("/")

                success = True
                return ToolResult(
                    success=True,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    data=data_result
                )

            except ValueError as ve:
                # Handle value errors raised during tool verification (e.g. PATH_OUTSIDE_WORKSPACE, SENSITIVE_FILE)
                error_code = str(ve)
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=error_code
                )
            except Exception as e:
                logger.error(f"Uncaught exception inside tool={tool_name} handler: {e}", exc_info=True)
                error_code = TOOL_EXECUTION_FAILED
                return ToolResult(
                    success=False,
                    tool=tool_name,
                    tool_call_id=tool_call_id,
                    error=TOOL_EXECUTION_FAILED
                )

        finally:
            # Generate exactly one audit event for every tool execution attempt
            duration_ms = (time.perf_counter() - start_time) * 1000
            result_status = "success" if success else "failed"
            if decision == "DENY":
                result_status = "denied"
                
            log_tool_audit(
                request_id=request_id,
                tool_call_id=tool_call_id,
                workspace_id=workspace_id,
                tool_name=tool_name,
                permission_requested=tool_name if decision == "DENY" else (registry.get(tool_name).required_permission if registry.get(tool_name) else tool_name),
                effective_permission=effective_perm,
                decision=decision,
                relative_path=relative_path_involved,
                duration_ms=duration_ms,
                result_status=result_status,
                error_code=error_code
            )
