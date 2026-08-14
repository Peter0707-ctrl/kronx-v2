"""
Phase 2F — Verification Error Codes & Exception
Standardized error codes and structured exception class for the verification engine.
"""
from __future__ import annotations

# Standardized Error Codes
WORKSPACE_NOT_AUTHORIZED     = "WORKSPACE_NOT_AUTHORIZED"
PATH_OUTSIDE_WORKSPACE       = "PATH_OUTSIDE_WORKSPACE"
VERIFICATION_NOT_FOUND       = "VERIFICATION_NOT_FOUND"
INVALID_VERIFICATION_REQUEST = "INVALID_VERIFICATION_REQUEST"
SECURITY_CHECK_FAILED        = "SECURITY_CHECK_FAILED"
INTEGRITY_CHECK_FAILED       = "INTEGRITY_CHECK_FAILED"
REGRESSION_DETECTED          = "REGRESSION_DETECTED"
TEST_FAILURE                 = "TEST_FAILURE"
RESOURCE_LIMIT               = "RESOURCE_LIMIT"
SENSITIVE_DATA_DETECTED      = "SENSITIVE_DATA_DETECTED"
UNSAFE_STATE                 = "UNSAFE_STATE"
READINESS_BLOCKED            = "READINESS_BLOCKED"
VERIFICATION_FAILED          = "VERIFICATION_FAILED"


class VerificationError(Exception):
    """Structured exception for verification engine failures."""
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail
