"""
Phase 2F — Verification Check Factories & Helpers
Generates standardized VerificationCheck objects with evidence dictionaries.
"""
from __future__ import annotations
import uuid
import time
from typing import Dict, Any, Optional

from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity


def create_check(
    category: str,
    name: str,
    status: CheckStatus,
    message: str,
    severity: CheckSeverity = CheckSeverity.INFO,
    evidence: Optional[Dict[str, Any]] = None,
    duration_ms: float = 0.0,
) -> VerificationCheck:
    """Helper to instantiate a VerificationCheck model."""
    check_id = f"chk_{category[:4].lower()}_{uuid.uuid4().hex[:6]}"
    return VerificationCheck(
        check_id=check_id,
        category=category,
        name=name,
        status=status,
        severity=severity,
        message=message,
        evidence=evidence or {},
        duration_ms=round(duration_ms, 2),
    )
