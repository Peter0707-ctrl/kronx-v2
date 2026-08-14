"""
Phase 2I.1 — Multimodal Intelligence & Creative Capability Errors
Standardized error codes and exception class.
"""
from typing import Optional, Dict, Any

# Standardized Error Codes
AUTH_REQUIRED              = "AUTH_REQUIRED"
WORKSPACE_NOT_AUTHORIZED   = "WORKSPACE_NOT_AUTHORIZED"
TENANT_NOT_AUTHORIZED      = "TENANT_NOT_AUTHORIZED"
INVALID_REQUEST            = "INVALID_REQUEST"
EMPTY_REQUEST              = "EMPTY_REQUEST"
UNSUPPORTED_FILE_TYPE      = "UNSUPPORTED_FILE_TYPE"
FILE_NOT_FOUND             = "FILE_NOT_FOUND"
FILE_TOO_LARGE             = "FILE_TOO_LARGE"
DOCUMENT_TOO_LARGE         = "DOCUMENT_TOO_LARGE"
IMAGE_TOO_LARGE            = "IMAGE_TOO_LARGE"
OCR_TOO_LARGE              = "OCR_TOO_LARGE"
TOO_MANY_FILES             = "TOO_MANY_FILES"
SENSITIVE_FILE_BLOCKED     = "SENSITIVE_FILE_BLOCKED"
SECRET_DETECTED            = "SECRET_DETECTED"
PATH_TRAVERSAL_DETECTED    = "PATH_TRAVERSAL_DETECTED"
PROMPT_INJECTION_DETECTED  = "PROMPT_INJECTION_DETECTED"
PERMISSION_DENIED          = "PERMISSION_DENIED"
FORBIDDEN_PERMISSION_LEVEL = "FORBIDDEN_PERMISSION_LEVEL"
CAPABILITY_UNAVAILABLE     = "CAPABILITY_UNAVAILABLE"
PROVIDER_ERROR             = "PROVIDER_ERROR"
RESOURCE_NOT_FOUND         = "RESOURCE_NOT_FOUND"
RATE_LIMIT_EXCEEDED        = "RATE_LIMIT_EXCEEDED"
OPERATION_CANCELLED        = "OPERATION_CANCELLED"
STORE_ERROR                = "STORE_ERROR"


class MultimodalError(Exception):
    """Base exception for all multimodal intelligence and creative operations."""
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }
