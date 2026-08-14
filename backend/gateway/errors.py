"""
Phase 2H — Gateway Error Codes & Standardized Exception
Defines all standardized gateway, rate limit, quota, and resource error codes.
"""
from __future__ import annotations

# Standard Gateway Error Codes
REQUEST_TOO_LARGE          = "REQUEST_TOO_LARGE"
INVALID_REQUEST            = "INVALID_REQUEST"
RATE_LIMITED               = "RATE_LIMITED"
QUOTA_EXCEEDED             = "QUOTA_EXCEEDED"
CONCURRENCY_LIMIT          = "CONCURRENCY_LIMIT"
ABUSE_LIMIT_REACHED        = "ABUSE_LIMIT_REACHED"
RESOURCE_NOT_FOUND         = "RESOURCE_NOT_FOUND"
SERVICE_UNAVAILABLE        = "SERVICE_UNAVAILABLE"
INTERNAL_ERROR             = "INTERNAL_ERROR"
AUTHENTICATION_REQUIRED    = "AUTHENTICATION_REQUIRED"
WORKSPACE_NOT_AUTHORIZED   = "WORKSPACE_NOT_AUTHORIZED"
TENANT_NOT_AUTHORIZED      = "TENANT_NOT_AUTHORIZED"
FORBIDDEN_PERMISSION_LEVEL = "FORBIDDEN_PERMISSION_LEVEL"
PATH_OUTSIDE_WORKSPACE     = "PATH_OUTSIDE_WORKSPACE"
SENSITIVE_FILE             = "SENSITIVE_FILE"
BLOCKED_REQUIRES_PERMISSION = "BLOCKED_REQUIRES_PERMISSION"


class GatewayError(Exception):
    """Structured exception for API Gateway operations and policy enforcements."""
    def __init__(self, code: str, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code
