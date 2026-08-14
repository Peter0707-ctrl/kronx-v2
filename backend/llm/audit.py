"""
Phase 2J — LLM Gateway Audit Logger
Thread-safe structured logging for inference events with strict credential and prompt scrubbing.
"""
from __future__ import annotations
import os
import json
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from llm.sanitizer import sanitize_log_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LLM_LOG_FILE = os.path.join(LOG_DIR, "llm_audit.log")

_logger = logging.getLogger("kronx.llm_audit")
_logger.setLevel(logging.INFO)
_logger.propagate = False

if not _logger.handlers:
    try:
        handler = RotatingFileHandler(
            LLM_LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        _logger.addHandler(handler)
    except Exception:
        pass


def log_llm_audit(
    request_id: str,
    tenant_id: str,
    provider: str,
    model: str,
    capability: str,
    status: str,
    duration_ms: float,
    input_token_count: int = 0,
    output_token_count: int = 0,
    risk_level: str = "NONE",
    reason_code: str = "",
):
    """
    Logs structured inference event metadata.
    PROMPT TEXT, FILE SECRETS, AND RAW RESPONSES ARE NEVER INCLUDED.
    """
    event = {
        "request_id": sanitize_log_message(request_id),
        "tenant_id": sanitize_log_message(tenant_id),
        "provider": sanitize_log_message(provider),
        "model": sanitize_log_message(model),
        "capability": sanitize_log_message(capability),
        "status": sanitize_log_message(status),
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else 0.0,
        "input_token_count": input_token_count,
        "output_token_count": output_token_count,
        "risk_level": sanitize_log_message(risk_level),
        "reason_code": sanitize_log_message(reason_code),
    }

    raw_json = json.dumps(event, separators=(",", ":"))
    _logger.info(f"[llm_audit] {raw_json}")
