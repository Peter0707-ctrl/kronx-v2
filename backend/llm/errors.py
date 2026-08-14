"""
Phase 2J — LLM Provider Gateway & Inference Engine Errors
Standardized error codes and exception types.
"""
from typing import Optional, Dict, Any

# Standardized Error Codes
UNAUTHORIZED = "UNAUTHORIZED"
FORBIDDEN = "FORBIDDEN"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
MODEL_TIMEOUT = "MODEL_TIMEOUT"
MODEL_RATE_LIMITED = "MODEL_RATE_LIMITED"
CAPABILITY_UNSUPPORTED = "CAPABILITY_UNSUPPORTED"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
MODEL_OUTPUT_BLOCKED = "MODEL_OUTPUT_BLOCKED"
PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
SECRET_DETECTED = "SECRET_DETECTED"
INFERENCE_CANCELLED = "INFERENCE_CANCELLED"
INVALID_REQUEST = "INVALID_REQUEST"
FORBIDDEN_PERMISSION_LEVEL = "FORBIDDEN_PERMISSION_LEVEL"
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
TOOL_INTENT_BLOCKED = "TOOL_INTENT_BLOCKED"
STREAM_ERROR = "STREAM_ERROR"


class LLMError(Exception):
    """Base exception for all Phase 2J LLM Gateway operations."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
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
