"""
Phase 2D — Execution Audit Trail
Structured audit logging for execution operations outside user workspaces.
Never logs secrets, file contents, passwords, or raw multi-line strings.
"""
from __future__ import annotations
import json
from typing import Optional

from utils.logger import logger

FORBIDDEN_AUDIT_KEYWORDS = ["password", "secret", "token", "key", "api_key", "bearer"]


def sanitize_audit_field(value: Any) -> str:
    """Sanitize strings by escaping newlines/carriage returns and truncating long values."""
    if value is None:
        return ""
    val_str = str(value).replace("\n", "\\n").replace("\r", "\\r")
    if len(val_str) > 500:
        val_str = val_str[:497] + "..."
    return val_str


def log_execution_audit(
    execution_id: str,
    request_id: str,
    workspace_id: str,
    plan_id: str,
    task_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    permission_level: str = "READ",
    status: str = "RUNNING",
    duration_ms: Optional[float] = None,
    error_code: Optional[str] = None,
) -> str:
    """
    Emits a structured [execution_audit] JSON entry to the application logger.
    Returns audit reference string.
    """
    audit_entry = {
        "execution_id": sanitize_audit_field(execution_id),
        "request_id": sanitize_audit_field(request_id),
        "workspace_id": sanitize_audit_field(workspace_id),
        "plan_id": sanitize_audit_field(plan_id),
        "task_id": sanitize_audit_field(task_id),
        "tool_name": sanitize_audit_field(tool_name),
        "permission_level": sanitize_audit_field(permission_level),
        "status": sanitize_audit_field(status),
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "error_code": sanitize_audit_field(error_code),
    }

    try:
        payload = json.dumps(audit_entry)
        logger.info(f"[execution_audit] {payload}")
    except Exception:
        pass

    return f"audit_exec_{execution_id}_{task_id or 'global'}"
