"""
Phase 2H — Gateway Audit Logging Engine
Structured logging for all gateway interactions with bounded file rotation and zero secret leakage.
"""
from __future__ import annotations
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
GATEWAY_LOG_FILE = os.path.join(LOGS_DIR, "gateway_audit.log")

os.makedirs(LOGS_DIR, exist_ok=True)

# Configure rotating file handler: max 5 MB per file, max 5 backup files
_gateway_logger = logging.getLogger("kronx.gateway_audit")
_gateway_logger.setLevel(logging.INFO)
_gateway_logger.propagate = False

if not _gateway_logger.handlers:
    rfh = RotatingFileHandler(
        GATEWAY_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    rfh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    _gateway_logger.addHandler(rfh)


def sanitize_str(val: Any) -> str:
    """Escapes newlines, carriage returns, tabs, and bounds string length."""
    if val is None:
        return ""
    s = str(val).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s[:256] if len(s) > 256 else s


def log_gateway_event(
    request_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    user_id: str = "",
    tenant_id: str = "",
    rate_limit_status: str = "OK",
    quota_status: str = "OK",
    operation: str = "REQUEST",
    reason: str = "",
):
    """Logs a structured JSON gateway event without exposing credentials or payload secrets."""
    event = {
        "request_id": sanitize_str(request_id),
        "user_id": sanitize_str(user_id),
        "tenant_id": sanitize_str(tenant_id),
        "endpoint": sanitize_str(endpoint),
        "method": sanitize_str(method),
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "rate_limit_status": sanitize_str(rate_limit_status),
        "quota_status": sanitize_str(quota_status),
        "operation": sanitize_str(operation),
        "reason": sanitize_str(reason),
    }
    try:
        payload = json.dumps(event)
        _gateway_logger.info(payload)
    except Exception:
        pass
