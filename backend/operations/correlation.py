"""
Phase 3.1 — Request Correlation & Trace Context
Provides sanitized, bounded request_id, correlation_id, and operation_id propagation.
"""
import re
import uuid
from typing import Optional
from fastapi import Request

MAX_ID_LENGTH = 64
_SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def sanitize_identifier(raw_id: Optional[str], default_prefix: str = "req") -> str:
    """Sanitizes an external or internal identifier to prevent injection and unbounded size."""
    if not raw_id or not isinstance(raw_id, str):
        return f"{default_prefix}_{uuid.uuid4().hex[:12]}"
    clean = raw_id.strip()[:MAX_ID_LENGTH]
    if _SAFE_ID_REGEX.match(clean):
        return clean
    # Strip forbidden characters
    stripped = re.sub(r"[^a-zA-Z0-9_\-\.]", "", clean)
    if not stripped:
        return f"{default_prefix}_{uuid.uuid4().hex[:12]}"
    return stripped[:MAX_ID_LENGTH]


def extract_correlation_context(request: Request) -> dict:
    """Extracts sanitized request_id and correlation_id from incoming HTTP headers."""
    req_id = sanitize_identifier(
        request.headers.get("X-Request-ID"),
        default_prefix="req"
    )
    corr_id = sanitize_identifier(
        request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID"),
        default_prefix="corr"
    )
    return {
        "request_id": req_id,
        "correlation_id": corr_id,
    }
