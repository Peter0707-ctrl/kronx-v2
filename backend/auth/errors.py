"""
Phase 2G — Authentication & Authorization Error Codes & Exception
Standardized error codes for identity, session, and multi-tenant authorization.
"""
from __future__ import annotations

# Standardized Error Codes
AUTHENTICATION_REQUIRED   = "AUTHENTICATION_REQUIRED"
INVALID_CREDENTIALS       = "INVALID_CREDENTIALS"
SESSION_EXPIRED           = "SESSION_EXPIRED"
SESSION_REVOKED           = "SESSION_REVOKED"
SESSION_INVALID           = "SESSION_INVALID"
USER_DISABLED             = "USER_DISABLED"
USER_ALREADY_EXISTS       = "USER_ALREADY_EXISTS"
USER_NOT_FOUND            = "USER_NOT_FOUND"
WORKSPACE_NOT_AUTHORIZED  = "WORKSPACE_NOT_AUTHORIZED"
TENANT_NOT_AUTHORIZED     = "TENANT_NOT_AUTHORIZED"
RESOURCE_NOT_AUTHORIZED   = "RESOURCE_NOT_AUTHORIZED"
RESOURCE_NOT_FOUND        = "RESOURCE_NOT_FOUND"
RATE_LIMITED              = "RATE_LIMITED"
ROLE_ESCALATION_BLOCKED   = "ROLE_ESCALATION_BLOCKED"
FORBIDDEN_PERMISSION_LEVEL = "FORBIDDEN_PERMISSION_LEVEL"
INVALID_AUTH_REQUEST      = "INVALID_AUTH_REQUEST"


class AuthError(Exception):
    """Structured exception for authentication and authorization errors."""
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail
