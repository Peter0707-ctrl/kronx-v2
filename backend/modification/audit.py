"""
Phase 2E — Structured Modification Audit Trail
Logs all proposal, approval, application, and rollback events outside user workspaces.
Never logs file contents, patch contents, passwords, or secret tokens.
"""
from __future__ import annotations
import json
from typing import Optional, Any

from utils.logger import logger


def sanitize_audit_str(val: Any) -> str:
    """Escapes newline and carriage return characters and truncates strings."""
    if val is None:
        return ""
    s = str(val).replace("\n", "\\n").replace("\r", "\\r")
    return s[:400] if len(s) > 400 else s


def log_modification_audit(
    modification_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
    authorization_id: Optional[str] = None,
    request_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    plan_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    task_id: Optional[str] = None,
    operation: str = "PROPOSE",
    status: str = "PROPOSED",
    permission: str = "WRITE",
    files_count: int = 0,
    bytes_written: int = 0,
    duration_ms: Optional[float] = None,
    error_code: Optional[str] = None,
) -> str:
    """
    Emits structured [modification_audit] JSON entry to application logger.
    Returns audit reference string.
    """
    audit_entry = {
        "modification_id": sanitize_audit_str(modification_id),
        "proposal_id": sanitize_audit_str(proposal_id),
        "authorization_id": sanitize_audit_str(authorization_id),
        "request_id": sanitize_audit_str(request_id),
        "workspace_id": sanitize_audit_str(workspace_id),
        "plan_id": sanitize_audit_str(plan_id),
        "execution_id": sanitize_audit_str(execution_id),
        "task_id": sanitize_audit_str(task_id),
        "operation": sanitize_audit_str(operation),
        "status": sanitize_audit_str(status),
        "permission": sanitize_audit_str(permission),
        "files_count": files_count,
        "bytes_written": bytes_written,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "error_code": sanitize_audit_str(error_code),
    }

    try:
        payload = json.dumps(audit_entry)
        logger.info(f"[modification_audit] {payload}")
    except Exception:
        pass

    return f"audit_mod_{modification_id or proposal_id or 'global'}"
