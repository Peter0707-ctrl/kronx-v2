"""
Phase 2I — Agent Error Codes & Exception
Defines standardized error codes and exception class for Agent Brain operations.
"""
from __future__ import annotations

AUTH_REQUIRED               = "AUTH_REQUIRED"
SESSION_EXPIRED             = "SESSION_EXPIRED"
SESSION_REVOKED             = "SESSION_REVOKED"
WORKSPACE_NOT_AUTHORIZED    = "WORKSPACE_NOT_AUTHORIZED"
TENANT_NOT_AUTHORIZED       = "TENANT_NOT_AUTHORIZED"
INTENT_UNCERTAIN            = "INTENT_UNCERTAIN"
CAPABILITY_NOT_REGISTERED   = "CAPABILITY_NOT_REGISTERED"
PERMISSION_REQUIRED         = "PERMISSION_REQUIRED"
FORBIDDEN_PERMISSION_LEVEL  = "FORBIDDEN_PERMISSION_LEVEL"
SENSITIVE_CONTENT           = "SENSITIVE_CONTENT"
PLAN_REQUIRED               = "PLAN_REQUIRED"
VERIFICATION_FAILED         = "VERIFICATION_FAILED"
INTEGRITY_FAILED            = "INTEGRITY_FAILED"
RATE_LIMITED                = "RATE_LIMITED"
QUOTA_EXCEEDED              = "QUOTA_EXCEEDED"
CONCURRENCY_LIMIT           = "CONCURRENCY_LIMIT"
AGENT_BLOCKED               = "AGENT_BLOCKED"
AGENT_NOT_FOUND             = "AGENT_NOT_FOUND"
INVALID_AGENT_REQUEST       = "INVALID_AGENT_REQUEST"
AGENT_CANCELLED             = "AGENT_CANCELLED"


class AgentError(Exception):
    """Structured exception for AI Agent Brain operations."""
    def __init__(self, code: str, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code
