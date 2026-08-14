"""
Phase 3.1 — Operations, Observability, Recovery & Lifecycle Schemas
Strict Pydantic models for all operational subsystems.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class LifecycleState(str, Enum):
    STARTING = "STARTING"
    READY    = "READY"
    DEGRADED = "DEGRADED"
    DRAINING = "DRAINING"
    STOPPING = "STOPPING"
    STOPPED  = "STOPPED"
    FAILED   = "FAILED"


class HealthStatus(str, Enum):
    HEALTHY   = "HEALTHY"
    DEGRADED  = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class ReadinessDecision(str, Enum):
    READY     = "READY"
    NOT_READY = "NOT_READY"
    BLOCKED   = "BLOCKED"


class Severity(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class JobStatus(str, Enum):
    QUEUED     = "QUEUED"
    RUNNING    = "RUNNING"
    PAUSED     = "PAUSED"
    CANCELLING = "CANCELLING"
    CANCELLED  = "CANCELLED"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"
    BLOCKED    = "BLOCKED"
    EXPIRED    = "EXPIRED"


class IncidentStatus(str, Enum):
    OPEN          = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED     = "MITIGATED"
    RESOLVED      = "RESOLVED"
    CLOSED        = "CLOSED"


class EventType(str, Enum):
    REQUEST_STARTED          = "REQUEST_STARTED"
    REQUEST_COMPLETED        = "REQUEST_COMPLETED"
    REQUEST_FAILED           = "REQUEST_FAILED"
    AUTH_FAILURE             = "AUTH_FAILURE"
    AUTH_SUCCESS             = "AUTH_SUCCESS"
    RATE_LIMITED             = "RATE_LIMITED"
    QUOTA_EXCEEDED           = "QUOTA_EXCEEDED"
    AGENT_STARTED            = "AGENT_STARTED"
    AGENT_COMPLETED          = "AGENT_COMPLETED"
    AGENT_BLOCKED            = "AGENT_BLOCKED"
    LLM_REQUEST              = "LLM_REQUEST"
    LLM_FAILURE              = "LLM_FAILURE"
    MODIFICATION_PROPOSED    = "MODIFICATION_PROPOSED"
    MODIFICATION_APPLIED     = "MODIFICATION_APPLIED"
    MODIFICATION_ROLLED_BACK = "MODIFICATION_ROLLED_BACK"
    VERIFICATION_STARTED     = "VERIFICATION_STARTED"
    VERIFICATION_COMPLETED   = "VERIFICATION_COMPLETED"
    SYSTEM_DEGRADED          = "SYSTEM_DEGRADED"
    SYSTEM_RECOVERED         = "SYSTEM_RECOVERED"
    BACKUP_STARTED           = "BACKUP_STARTED"
    BACKUP_COMPLETED         = "BACKUP_COMPLETED"
    BACKUP_FAILED            = "BACKUP_FAILED"
    RECOVERY_STARTED         = "RECOVERY_STARTED"
    RECOVERY_COMPLETED       = "RECOVERY_COMPLETED"
    RECOVERY_FAILED          = "RECOVERY_FAILED"
    INCIDENT_CREATED         = "INCIDENT_CREATED"
    INCIDENT_RESOLVED        = "INCIDENT_RESOLVED"


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class LifecycleStatus(BaseModel):
    state:        LifecycleState
    active_jobs:  int = 0
    draining:     bool = False
    started_at:   str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at:   str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details:      str = "System operating normally."


class HealthComponent(BaseModel):
    name:         str
    status:       HealthStatus
    message:      str = "OK"
    details:      Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    status:       HealthStatus
    components:   Dict[str, HealthComponent]
    timestamp:    str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReadinessEvaluation(BaseModel):
    decision:     ReadinessDecision
    score:        float = 10.0
    checks:       List[Dict[str, Any]] = Field(default_factory=list)
    timestamp:    str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OperationalEvent(BaseModel):
    event_id:       str
    timestamp:      str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type:     EventType
    severity:       Severity = Severity.LOW
    request_id:     Optional[str] = None
    correlation_id: Optional[str] = None
    tenant_id:      Optional[str] = None
    metadata:       Dict[str, Any] = Field(default_factory=dict)


class DiagnosticCheck(BaseModel):
    check_id:     str
    name:         str
    category:     str
    passed:       bool
    message:      str
    duration_ms:  float = 0.0


class DiagnosticReport(BaseModel):
    diagnostic_id: str
    timestamp:     str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_checks:  int
    passed_checks: int
    failed_checks: int
    checks:        List[DiagnosticCheck]
    system_health: HealthStatus


class StoreIntegrityRecord(BaseModel):
    store_name:    str
    exists:        bool
    valid_json:    bool
    sha256:        str
    record_count:  int = 0
    size_bytes:    int = 0
    corrupted:     bool = False
    error_message: Optional[str] = None


class BackupRecord(BaseModel):
    backup_id:         str
    timestamp:         str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    store_name:        str
    sha256:            str
    size_bytes:        int
    status:            str = "COMPLETED"
    tenant_scope:      Optional[str] = None
    backup_filename:   str


class RecoveryRequest(BaseModel):
    backup_id:         str
    store_name:        str
    target_tenant_id:  Optional[str] = None


class RecoveryResult(BaseModel):
    status:              str
    backup_id:           str
    store_name:          str
    restored_records:    int
    verification_passed: bool
    timestamp:           str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobRecord(BaseModel):
    job_id:        str
    tenant_id:     str
    job_type:      str
    status:        JobStatus = JobStatus.QUEUED
    progress:      float = 0.0
    created_at:    str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at:    str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at:  Optional[str] = None
    error:         Optional[str] = None
    metadata:      Dict[str, Any] = Field(default_factory=dict)


class IncidentRecord(BaseModel):
    incident_id:      str
    title:            str
    description:      str
    severity:         Severity
    status:           IncidentStatus = IncidentStatus.OPEN
    source:           str = "SYSTEM"
    tenant_id:        Optional[str] = None
    created_at:       str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at:      Optional[str] = None
    resolution_notes: Optional[str] = None


class ConfigValidationResult(BaseModel):
    status:       HealthStatus
    is_valid:     bool
    summary:      Dict[str, str]
    errors:       List[str] = Field(default_factory=list)


class DashboardData(BaseModel):
    lifecycle:             LifecycleStatus
    health:                HealthCheckResult
    readiness:             ReadinessEvaluation
    metrics:               Dict[str, Any]
    active_jobs_count:     int
    open_incidents_count:  int
    latest_backup:         Optional[BackupRecord] = None
    recent_events:         List[OperationalEvent] = Field(default_factory=list)
