import os
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import threading

# Define path to tools_audit.log outside the user workspace (located in backend/logs/)
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "tools_audit.log")

_audit_lock = threading.Lock()

# Setup rotating file logger specifically for audit
_audit_logger = logging.getLogger("kronx_tools_audit")
_audit_logger.setLevel(logging.INFO)
# Clear existing handlers to prevent duplicate writes
_audit_logger.handlers = []

_handler = RotatingFileHandler(AUDIT_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
_formatter = logging.Formatter('%(message)s')
_handler.setFormatter(_formatter)
_audit_logger.addHandler(_handler)

def sanitize_for_log(value: str) -> str:
    """Sanitize strings by replacing newlines to prevent audit log injection."""
    if not isinstance(value, str):
        return str(value)
    return value.replace("\n", " ").replace("\r", " ").strip()

def log_tool_audit(
    request_id: str,
    tool_call_id: str,
    workspace_id: str,
    tool_name: str,
    permission_requested: str,
    effective_permission: str,
    decision: str,
    relative_path: str,
    duration_ms: float,
    result_status: str,
    error_code: str = None
):
    """
    Log tool execution audit event cleanly.
    Excludes sensitive files contents and sanitizes newline injections.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "request_id": sanitize_for_log(request_id),
        "tool_call_id": sanitize_for_log(tool_call_id),
        "workspace_id": sanitize_for_log(workspace_id),
        "tool_name": sanitize_for_log(tool_name),
        "permission_requested": sanitize_for_log(permission_requested),
        "effective_permission": sanitize_for_log(effective_permission),
        "decision": sanitize_for_log(decision),
        "relative_path": sanitize_for_log(relative_path or ""),
        "duration_ms": round(duration_ms, 2),
        "result_status": sanitize_for_log(result_status),
        "error_code": sanitize_for_log(error_code or "")
    }
    
    with _audit_lock:
        _audit_logger.info(json.dumps(event))
        for handler in _audit_logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass
