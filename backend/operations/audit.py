"""
Phase 3.1 — Structured Operations Audit Logging
Logs operations, lifecycle, metrics, and incident events in structured JSON format with zero secret exposure.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from utils.logger import logger
from llm.sanitizer import sanitize_secrets



def log_operations_audit(
    action: str,
    status: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Emits a structured [operations_audit] JSON log record with sanitized secrets."""
    rec: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_type": "operations_audit",
        "action": action,
        "status": status,
        "tenant_id": tenant_id or "system",
        "user_id": user_id or "system",
        "request_id": request_id or "",
        "correlation_id": correlation_id or "",
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "error_code": error_code or "",
    }
    if details:
        safe_details = {}
        for k, v in details.items():
            if isinstance(v, str):
                safe_details[k] = sanitize_secrets(v)
            else:
                safe_details[k] = v
        rec["details"] = safe_details

    clean_json = sanitize_secrets(json.dumps(rec))
    logger.info(f"[operations_audit] {clean_json}")
