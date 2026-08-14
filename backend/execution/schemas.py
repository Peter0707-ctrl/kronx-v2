"""
Phase 2D — Execution Schemas
Strict Pydantic models and resource limits for the Safe Autonomous Execution Orchestration Engine.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------
# Enumerations
# ------------------------------------------------------------------

class ExecutionMode(str, Enum):
    DRY_RUN = "DRY_RUN"
    RUN     = "RUN"

class ExecutionStatus(str, Enum):
    QUEUED    = "QUEUED"
    RUNNING   = "RUNNING"
    PAUSED    = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED   = "BLOCKED"

class TaskExecutionStatus(str, Enum):
    PENDING   = "PENDING"
    READY     = "READY"
    RUNNING   = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED    = "FAILED"
    BLOCKED   = "BLOCKED"
    SKIPPED   = "SKIPPED"
    CANCELLED = "CANCELLED"

# ------------------------------------------------------------------
# Resource Limits
# ------------------------------------------------------------------
MAX_TASKS_PER_EXECUTION     = 100
MAX_TOOL_CALLS_PER_TASK     = 20
MAX_TOTAL_TOOL_CALLS        = 500
MAX_RETRY_ATTEMPTS          = 3
MAX_EXECUTION_TIME_SECONDS  = 300
MAX_RESULT_SIZE_BYTES       = 1 * 1024 * 1024  # 1 MB

# ------------------------------------------------------------------
# Request Model
# ------------------------------------------------------------------

class ExecutionRequest(BaseModel):
    request_id:          str
    workspace_id:        str
    plan_id:             str
    confirmation_token:  Optional[str] = None
    requested_task_ids:  Optional[List[str]] = None
    execution_mode:      ExecutionMode = ExecutionMode.DRY_RUN
    user_id:             Optional[str] = None
    session_id:          Optional[str] = None
    tenant_id:           Optional[str] = None

    @field_validator("requested_task_ids")
    @classmethod
    def validate_task_count(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > MAX_TASKS_PER_EXECUTION:
            raise ValueError(f"Too many requested tasks (max {MAX_TASKS_PER_EXECUTION}).")
        return v

# ------------------------------------------------------------------
# Task State Model
# ------------------------------------------------------------------

class ExecutionTaskState(BaseModel):
    task_id:              str
    title:                str
    description:          str
    status:               TaskExecutionStatus = TaskExecutionStatus.PENDING
    dependencies:         List[str] = Field(default_factory=list)
    required_tools:       List[str] = Field(default_factory=list)
    required_permissions: List[str] = Field(default_factory=list)
    risk_level:           str = "LOW"
    attempts:             int = 0
    started_at:           Optional[str] = None
    completed_at:         Optional[str] = None
    result_summary:       Optional[str] = None
    error:                Optional[str] = None
    tool_results:         List[Dict[str, Any]] = Field(default_factory=list)

# ------------------------------------------------------------------
# Checkpoint Model
# ------------------------------------------------------------------

class ExecutionCheckpoint(BaseModel):
    execution_id: str
    plan_id:      str
    workspace_id: str
    status:       ExecutionStatus
    timestamp:    str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    tasks:        List[ExecutionTaskState] = Field(default_factory=list)
    metadata:     Dict[str, Any] = Field(default_factory=dict)

# ------------------------------------------------------------------
# Result Model
# ------------------------------------------------------------------

class ExecutionResult(BaseModel):
    execution_id:         str
    plan_id:              str
    workspace_id:         str
    status:               ExecutionStatus
    execution_mode:       ExecutionMode
    completed_tasks:      List[str] = Field(default_factory=list)
    blocked_tasks:        List[str] = Field(default_factory=list)
    failed_tasks:         List[str] = Field(default_factory=list)
    skipped_tasks:        List[str] = Field(default_factory=list)
    tasks:                List[ExecutionTaskState] = Field(default_factory=list)
    verification_results: List[Dict[str, Any]] = Field(default_factory=list)
    audit_reference:      str
    created_at:           str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    completed_at:         Optional[str] = None
    duration_ms:          Optional[float] = None
    user_id:              Optional[str] = None
    session_id:           Optional[str] = None
    tenant_id:            Optional[str] = None

    class Config:
        use_enum_values = True
