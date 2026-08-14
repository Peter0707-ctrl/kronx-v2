"""
Phase 2G — Multi-Tenant Authorization Engine
Enforces tenant isolation, workspace ownership, and object ownership across all Kron-X systems.
Guarantees that workspace_id or object_id alone cannot bypass tenant and ownership gates.
"""
from __future__ import annotations
import time
from typing import Optional, Dict, Any

from auth.schemas import AuthenticationContext, UserRole
from auth.errors import (
    AuthError,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    RESOURCE_NOT_AUTHORIZED,
    RESOURCE_NOT_FOUND,
    ROLE_ESCALATION_BLOCKED,
    FORBIDDEN_PERMISSION_LEVEL,
)
from auth.audit import log_auth_audit
from workspace.store import WorkspaceStore


class MultiTenantAuthorizer:
    """Authorizes user access to workspaces and multi-tenant domain objects."""

    def __init__(self, ws_store: Optional[WorkspaceStore] = None):
        self._ws_store = ws_store or WorkspaceStore()

    def authorize_workspace_access(
        self,
        context: AuthenticationContext,
        workspace_id: str,
    ) -> Dict[str, Any]:
        """
        Validates that the authenticated user and tenant are authorized to access the specified workspace.
        Returns the workspace dictionary on success.
        Raises AuthError on any failure.
        """
        start_t = time.perf_counter()

        if not workspace_id:
            raise AuthError(WORKSPACE_NOT_AUTHORIZED, "Workspace ID is required.")

        ws_data = self._ws_store.get_workspace(workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            dur = (time.perf_counter() - start_t) * 1000
            log_auth_audit(
                request_id=context.request_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                action="AUTHORIZE_WORKSPACE",
                resource_type="WORKSPACE",
                status="DENIED",
                duration_ms=dur,
                reason_code=WORKSPACE_NOT_AUTHORIZED,
                session_id=context.session_id,
            )
            raise AuthError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{workspace_id}' is not authorized.")

        # Multi-Tenant Isolation Check
        ws_tenant = ws_data.get("tenant_id")
        if ws_tenant and ws_tenant != context.tenant_id and context.role != UserRole.ADMIN:
            dur = (time.perf_counter() - start_t) * 1000
            log_auth_audit(
                request_id=context.request_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                action="AUTHORIZE_WORKSPACE",
                resource_type="WORKSPACE",
                status="DENIED",
                duration_ms=dur,
                reason_code=WORKSPACE_NOT_AUTHORIZED,
                session_id=context.session_id,
            )
            raise AuthError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{workspace_id}' is not authorized.")

        # User Ownership Check (if owner_user_id is recorded)
        ws_owner = ws_data.get("owner_user_id")
        if ws_owner and ws_owner != context.user_id and context.role not in (UserRole.ADMIN, UserRole.OWNER):
            dur = (time.perf_counter() - start_t) * 1000
            log_auth_audit(
                request_id=context.request_id,
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                action="AUTHORIZE_WORKSPACE",
                resource_type="WORKSPACE",
                status="DENIED",
                duration_ms=dur,
                reason_code=WORKSPACE_NOT_AUTHORIZED,
                session_id=context.session_id,
            )
            raise AuthError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{workspace_id}' is not authorized.")

        dur = (time.perf_counter() - start_t) * 1000
        log_auth_audit(
            request_id=context.request_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            action="AUTHORIZE_WORKSPACE",
            resource_type="WORKSPACE",
            status="ALLOWED",
            duration_ms=dur,
            session_id=context.session_id,
        )
        return ws_data

    def authorize_object_access(
        self,
        context: AuthenticationContext,
        obj_data: Optional[Dict[str, Any]],
        object_type: str,
    ) -> Dict[str, Any]:
        """
        Validates that a domain object (plan, execution, proposal, verification) belongs to the tenant.
        Sanitizes unauthorized attempts to return RESOURCE_NOT_FOUND to avoid leaking existence.
        """
        if not obj_data:
            raise AuthError(RESOURCE_NOT_FOUND, f"{object_type} not found.")

        obj_tenant = obj_data.get("tenant_id")
        if obj_tenant and obj_tenant != context.tenant_id and context.role != UserRole.ADMIN:
            raise AuthError(RESOURCE_NOT_FOUND, f"{object_type} not found.")

        # Also verify workspace access if workspace_id is attached to object
        ws_id = obj_data.get("workspace_id")
        if ws_id:
            self.authorize_workspace_access(context, ws_id)

        return obj_data

    @staticmethod
    def validate_no_role_escalation(requested_role: str) -> None:
        """Ensures client/AI cannot grant themselves elevated roles."""
        if requested_role in ("ADMIN", "OWNER", "EXECUTE", "NETWORK"):
            raise AuthError(ROLE_ESCALATION_BLOCKED, f"Cannot self-grant role '{requested_role}'.")
