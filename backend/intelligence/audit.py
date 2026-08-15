"""
Phase 4.0 — Intelligence Audit Logger
Logs structured operational decisions, evidence retrievals, and claims with automatic secret scrubbing.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json
from utils.logger import logger
from llm.sanitizer import sanitize_secrets


def log_intelligence_audit(
    task_id: str,
    request_id: str,
    tenant_id: str,
    action: str,
    status: str,
    intent: str,
    domain: str,
    duration_ms: Optional[float] = None,
    error_code: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Logs structured JSON audit records for the intelligence orchestrator."""
    audit_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_type": "intelligence_audit",
        "task_id": task_id,
        "request_id": request_id,
        "tenant_id": tenant_id,
        "action": action,
        "status": status,
        "intent": intent,
        "domain": domain,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "error_code": error_code,
        "details": details or {},
    }

    try:
        raw_json = json.dumps(audit_data)
        safe_json = sanitize_secrets(raw_json)
        logger.info(f"[intelligence_audit] {safe_json}")
    except Exception as e:
        logger.error(f"[intelligence_audit] Failed to serialize audit log: {e}")
