"""
Phase 4.0 — Intelligence Errors & Standard Codes
Defines standardized exception codes and error classes for the Copetra Intelligence Subsystem.
"""
from typing import Optional, Dict, Any

# Standard Intelligence Error Codes
INTENT_UNRESOLVED = "INTENT_UNRESOLVED"
CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
EVIDENCE_EXTRACTION_FAILED = "EVIDENCE_EXTRACTION_FAILED"
CLAIM_UNSUPPORTED = "CLAIM_UNSUPPORTED"
TOPIC_DRIFT_DETECTED = "TOPIC_DRIFT_DETECTED"
UNAUTHORIZED_CAPABILITY = "UNAUTHORIZED_CAPABILITY"
PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
ROUTING_FAILED = "ROUTING_FAILED"
TASK_NOT_FOUND = "TASK_NOT_FOUND"
TASK_CANCELLED = "TASK_CANCELLED"
TASK_ALREADY_COMPLETED = "TASK_ALREADY_COMPLETED"
PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
MULTIMODAL_MISMATCH = "MULTIMODAL_MISMATCH"
VALIDATION_FAILED = "VALIDATION_FAILED"


class IntelligenceError(Exception):
    """Base exception for Copetra Intelligence Subsystem with strict error codes."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }
