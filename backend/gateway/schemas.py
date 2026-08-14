"""
Phase 2H — Gateway Schemas & Models
Pydantic schemas for health status, metrics snapshot, quota reporting, and gateway payloads.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HealthState(str, Enum):
    LIVE     = "LIVE"
    READY    = "READY"
    DEGRADED = "DEGRADED"
    BLOCKED  = "BLOCKED"


class HealthCheckResponse(BaseModel):
    status:      HealthState
    version:     str = "2.0.0"
    environment: str
    uptime_sec:  float
    components:  Dict[str, str] = Field(default_factory=dict)


class QuotaUsage(BaseModel):
    tenant_id:            str
    active_sessions:      int = 0
    registered_workspaces: int = 0
    concurrent_jobs:      int = 0
    stored_plans:         int = 0
    stored_executions:    int = 0
    stored_modifications: int = 0
    stored_verifications: int = 0


class MetricSnapshot(BaseModel):
    requests_total:          int = 0
    errors_total:            int = 0
    auth_failures_total:     int = 0
    authz_failures_total:    int = 0
    rate_limited_total:      int = 0
    quota_exceeded_total:    int = 0
    concurrency_rejections:  int = 0
    avg_latency_ms:          float = 0.0
    endpoint_counts:         Dict[str, int] = Field(default_factory=dict)


class AbuseRecord(BaseModel):
    identifier:     str
    violation_count: int
    first_seen:     float
    last_seen:      float
    blocked_until:  float = 0.0
