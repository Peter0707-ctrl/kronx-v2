"""
Phase 2F — Verification Schemas & Models
Strict Pydantic models and bounded resource constants for verification and production readiness.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------
# Enumerations
# ------------------------------------------------------------------

class CheckStatus(str, Enum):
    PASS    = "PASS"
    FAIL    = "FAIL"
    WARN    = "WARN"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class CheckSeverity(str, Enum):
    INFO     = "INFO"
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class OverallVerificationStatus(str, Enum):
    PASSED               = "PASSED"
    PASSED_WITH_WARNINGS = "PASSED_WITH_WARNINGS"
    FAILED               = "FAILED"
    BLOCKED              = "BLOCKED"


class VerificationType(str, Enum):
    FULL       = "FULL"
    SECURITY   = "SECURITY"
    WORKSPACE  = "WORKSPACE"
    INTEGRITY  = "INTEGRITY"
    REGRESSION = "REGRESSION"
    HEALTH     = "HEALTH"
    READINESS  = "READINESS"


class ReadinessDecision(str, Enum):
    READY               = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY           = "NOT_READY"
    BLOCKED             = "BLOCKED"

# ------------------------------------------------------------------
# Resource Limits
# ------------------------------------------------------------------
MAX_VERIFICATION_FILES   = 5000
MAX_VERIFICATION_BYTES   = 100 * 1024 * 1024  # 100 MB
MAX_CHECKS               = 500
MAX_STORED_VERIFICATIONS = 500

# ------------------------------------------------------------------
# Verification Check Model
# ------------------------------------------------------------------

class VerificationCheck(BaseModel):
    check_id:    str
    category:    str
    name:        str
    status:      CheckStatus
    severity:    CheckSeverity = CheckSeverity.INFO
    message:     str
    evidence:    Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0

    class Config:
        use_enum_values = True

# ------------------------------------------------------------------
# Request Model
# ------------------------------------------------------------------

class VerificationRequest(BaseModel):
    request_id:               str
    workspace_id:             str
    verification_type:        VerificationType = VerificationType.FULL
    plan_id:                  Optional[str] = None
    execution_id:             Optional[str] = None
    modification_id:          Optional[str] = None
    include_tests:            bool = True
    include_security_checks:   bool = True
    include_integrity_checks:  bool = True
    include_health_checks:     bool = True
    user_id:                  Optional[str] = None
    session_id:               Optional[str] = None
    tenant_id:                Optional[str] = None

# ------------------------------------------------------------------
# Result Model
# ------------------------------------------------------------------

class VerificationResult(BaseModel):
    verification_id:    str
    workspace_id:       str
    status:             OverallVerificationStatus
    summary:            str
    checks:             List[VerificationCheck] = Field(default_factory=list)
    security_score:     float = 10.0
    integrity_score:    float = 10.0
    test_score:         float = 10.0
    readiness_score:    float = 10.0
    readiness_decision: ReadinessDecision = ReadinessDecision.READY
    regressions:        List[str] = Field(default_factory=list)
    critical_findings:  List[str] = Field(default_factory=list)
    warnings:           List[str] = Field(default_factory=list)
    recommendations:    List[str] = Field(default_factory=list)
    created_at:         str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    completed_at:       Optional[str] = None
    duration_ms:        Optional[float] = None
    audit_reference:    str = ""

    class Config:
        use_enum_values = True
