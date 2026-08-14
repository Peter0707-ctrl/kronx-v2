"""
Phase 2I — Agent Audit Logging Engine
Structured logging for all agent operations with file rotation and zero secret leakage.
"""
from __future__ import annotations
import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
AGENT_LOG_FILE = os.path.join(LOGS_DIR, "agent_audit.log")

os.makedirs(LOGS_DIR, exist_ok=True)

_agent_logger = logging.getLogger("kronx.agent_audit")
_agent_logger.setLevel(logging.INFO)
_agent_logger.propagate = False

if not _agent_logger.handlers:
    rfh = RotatingFileHandler(
        AGENT_LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    rfh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    _agent_logger.addHandler(rfh)


def sanitize_str(val: Any) -> str:
    """Escapes newlines, carriage returns, tabs, and bounds string length."""
    if val is None:
        return ""
    s = str(val).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return s[:256] if len(s) > 256 else s


def log_agent_audit(
    agent_id: str,
    request_id: str,
    tenant_id: str,
    user_id: str,
    workspace_id: str,
    intent: str,
    status: str,
    duration_ms: float,
    plan_id: str = "",
    modification_id: str = "",
    verification_id: str = "",
    reason: str = "",
):
    """Emits structured [agent_audit] JSON record without sensitive details."""
    record = {
        "agent_id": sanitize_str(agent_id),
        "request_id": sanitize_str(request_id),
        "tenant_id": sanitize_str(tenant_id),
        "user_id": sanitize_str(user_id),
        "workspace_id": sanitize_str(workspace_id),
        "intent": sanitize_str(intent),
        "status": sanitize_str(status),
        "duration_ms": round(duration_ms, 2),
        "plan_id": sanitize_str(plan_id),
        "modification_id": sanitize_str(modification_id),
        "verification_id": sanitize_str(verification_id),
        "reason": sanitize_str(reason),
    }
    try:
        payload = json.dumps(record)
        _agent_logger.info(f"[agent_audit] {payload}")
    except Exception:
        pass
