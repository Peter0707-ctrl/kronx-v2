"""
Phase 2F — Structured Verification Audit Trail
Logs all verification runs outside user workspaces.
Never logs file contents, passwords, or secret tokens; sanitizes newlines.
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
    return s[:400] if len(s) > 400 else s


def log_verification_audit(
    verification_id: str,
    request_id: str,
    workspace_id: str,
    status: str,
    duration_ms: float,
    check_count: int,
    critical_count: int,
    warning_count: int,
    readiness_decision: str,
) -> str:
    """
    Emits structured [verification_audit] JSON entry to application logger.
    Returns audit reference string.
    """
    audit_entry = {
        "verification_id": sanitize_str(verification_id),
        "request_id": sanitize_str(request_id),
        "workspace_id": sanitize_str(workspace_id),
        "status": sanitize_str(status),
        "duration_ms": round(duration_ms, 2),
        "check_count": check_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "readiness_decision": sanitize_str(readiness_decision),
    }

    try:
        payload = json.dumps(audit_entry)
        logger.info(f"[verification_audit] {payload}")
    except Exception:
        pass

    return f"audit_ver_{verification_id}"
