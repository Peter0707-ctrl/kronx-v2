"""
Phase 2G — Authentication & Authorization Audit Trail
Logs all authentication and authorization events to application audit.
Never logs passwords, password hashes, raw bearer tokens, or secret credentials; sanitizes newlines.
"""
from __future__ import annotations
import json
from typing import Optional, Any

from utils.logger import logger


def sanitize_str(val: Any) -> str:
    """Escapes newline and carriage return characters and truncates strings."""
    if val is None:
        return ""
    s = str(val).replace("\n", "\\n").replace("\r", "\\r")
    return s[:200] if len(s) > 200 else s


def log_auth_audit(
    request_id: str,
    user_id: str,
    tenant_id: str,
    action: str,
    resource_type: str,
    status: str,
    duration_ms: float,
    reason_code: str = "",
    session_id: str = "",
) -> None:
    """
    Emits a structured [auth_audit] JSON record without sensitive details.
    """
    audit_entry = {
        "request_id": sanitize_str(request_id),
        "session_id": sanitize_str(session_id[:12] if session_id else ""),
        "user_id": sanitize_str(user_id),
        "tenant_id": sanitize_str(tenant_id),
        "action": sanitize_str(action),
        "resource_type": sanitize_str(resource_type),
        "status": sanitize_str(status),
        "duration_ms": round(duration_ms, 2),
        "reason_code": sanitize_str(reason_code),
    }

    try:
        payload = json.dumps(audit_entry)
        logger.info(f"[auth_audit] {payload}")
    except Exception:
        pass
