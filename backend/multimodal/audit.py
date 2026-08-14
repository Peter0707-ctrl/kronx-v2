"""
Phase 2I.1 — Multimodal Structured Audit Logger
Records high-integrity, sanitized audit events to rotating log files.
"""
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

from multimodal.sanitizer import sanitize_log_message

MULTIMODAL_AUDIT_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "multimodal_audit.log"
)

os.makedirs(os.path.dirname(MULTIMODAL_AUDIT_LOG_FILE), exist_ok=True)

# Dedicated rotating audit logger (5MB, 5 backups)
_logger = logging.getLogger("kronx_multimodal_audit")
_logger.setLevel(logging.INFO)
_logger.propagate = False

if not _logger.handlers:
    _handler = RotatingFileHandler(
        MULTIMODAL_AUDIT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    _formatter = logging.Formatter("%(asctime)s - %(message)s")
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)


def log_multimodal_audit(
    request_id: str,
    tenant_id: str,
    workspace_id: str,
    operation: str,
    status: str,
    agent_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    input_type: Optional[str] = None,
    provider_type: Optional[str] = None,
    result_size: Optional[int] = None,
    risk_level: Optional[str] = "LOW",
    error_code: Optional[str] = None,
) -> None:
    """
    Logs structured multimodal audit event with strict newline and secret sanitization.
    """
    record = {
        "event": "multimodal_audit",
        "request_id": sanitize_log_message(request_id),
        "agent_id": sanitize_log_message(agent_id or ""),
        "tenant_id": sanitize_log_message(tenant_id),
        "workspace_id": sanitize_log_message(workspace_id),
        "operation": sanitize_log_message(operation),
        "status": sanitize_log_message(status),
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "input_type": sanitize_log_message(input_type or ""),
        "provider_type": sanitize_log_message(provider_type or "mock"),
        "result_size": result_size or 0,
        "risk_level": sanitize_log_message(risk_level or "LOW"),
        "error_code": sanitize_log_message(error_code or ""),
    }

    try:
        raw_json = json.dumps(record, default=str)
        # Ensure single-line log format
        clean_entry = raw_json.replace("\n", " ").replace("\r", "")
        _logger.info(f"[multimodal_audit] {clean_entry}")
    except Exception:
        pass
