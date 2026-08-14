"""
Phase 2D — Execution Authorization & Permission Gate
Multi-tenant aware authorization layer ensuring default-deny enforcement.
Never allows AI self-grant of permissions; checks against Phase 2B PermissionEngine.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any

from tools.permissions import PermissionEngine
from tools.registry import registry
from execution.errors import (
    BLOCKED_REQUIRES_PERMISSION,
    FORBIDDEN_PERMISSION_LEVEL,
    INVALID_PERMISSION_LEVEL,
    ExecutionError,
)

# Known dangerous tools that require elevated permissions
WRITE_TOOLS = frozenset(["create_file", "edit_file", "write_file", "delete_file"])
EXEC_TOOLS  = frozenset(["execute_command", "run_script", "spawn_process"])
NET_TOOLS   = frozenset(["network_request", "fetch_url", "http_post"])


class ExecutionAuthorizer:
    """
    Authorization and permission validator for task execution.
    Prepares for multi-tenancy (user_id, session_id, tenant_id).
    """

    def __init__(self):
        self._permission_engine = PermissionEngine()

    def authorize_task_tools(
        self,
        task_id: str,
        required_tools: List[str],
        effective_permission: str = "READ",
        confirmation_token: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, List[str]]:
        """
        Validates if all tools in a task are authorized under current permission level.
        Returns (is_authorized, status_code, blocked_tools).
        """
        context = context or {}
        blocked_tools: List[str] = []

        # Default effective permission is READ unless explicitly authorized
        current_eff = effective_permission.upper() if effective_permission else "READ"

        # Check for each tool required
        for tool_name in required_tools:
            # 1. Lookup in ToolRegistry if available
            descriptor = registry.get(tool_name)
            if descriptor:
                req_perm = descriptor.required_permission.upper()
            else:
                # Infer from tool name heuristics
                if tool_name in WRITE_TOOLS:
                    req_perm = "WRITE"
                elif tool_name in EXEC_TOOLS:
                    req_perm = "EXECUTE"
                elif tool_name in NET_TOOLS:
                    req_perm = "NETWORK"
                else:
                    req_perm = "READ"

            # 2. Check permission with PermissionEngine
            allowed, reason = self._permission_engine.validate_permission(req_perm, current_eff)

            if not allowed:
                blocked_tools.append(tool_name)
                if reason == "FORBIDDEN_PERMISSION_LEVEL" or req_perm == "ADMIN":
                    return False, FORBIDDEN_PERMISSION_LEVEL, blocked_tools
                return False, BLOCKED_REQUIRES_PERMISSION, blocked_tools

        return True, "ALLOWED", []

    def check_permission(
        self,
        required_permission: str,
        effective_permission: str = "READ",
    ) -> Tuple[bool, str]:
        """Direct check of a required permission level against effective permission."""
        req = required_permission.upper()
        eff = effective_permission.upper()
        
        if req == "ADMIN":
            return False, FORBIDDEN_PERMISSION_LEVEL
            
        allowed, reason = self._permission_engine.validate_permission(req, eff)
        if not allowed:
            if reason == "FORBIDDEN_PERMISSION_LEVEL":
                return False, FORBIDDEN_PERMISSION_LEVEL
            return False, BLOCKED_REQUIRES_PERMISSION
        return True, "ALLOWED"
