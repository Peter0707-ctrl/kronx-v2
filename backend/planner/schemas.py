"""
Phase 2C — Planner Schemas
Strict Pydantic models for all planning request/result types.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------
# Enumerations
# ------------------------------------------------------------------

class PlanningMode(str, Enum):
    ANALYZE  = "ANALYZE"
    DESIGN   = "DESIGN"
    DEBUG    = "DEBUG"
    REFACTOR = "REFACTOR"
    REVIEW   = "REVIEW"
    DOCUMENT = "DOCUMENT"

class TaskType(str, Enum):
    INSPECT             = "INSPECT"
    ANALYZE             = "ANALYZE"
    DESIGN              = "DESIGN"
    VERIFY              = "VERIFY"
    DOCUMENT            = "DOCUMENT"
    WAIT_FOR_PERMISSION = "WAIT_FOR_PERMISSION"

class TaskStatus(str, Enum):
    PENDING  = "PENDING"
    BLOCKED  = "BLOCKED"
    COMPLETE = "COMPLETE"

class RiskLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"

class ComplexityLevel(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"

class PermissionRequirement(str, Enum):
    ALLOWED                  = "ALLOWED"
    REQUIRES_EXPLICIT_PERMISSION = "REQUIRES_EXPLICIT_PERMISSION"
    BLOCKED                  = "BLOCKED"
    FORBIDDEN                = "FORBIDDEN"

# ------------------------------------------------------------------
# Resource limits (enforced at validation layer)
# ------------------------------------------------------------------
MAX_OBJECTIVE_LENGTH      = 4000
MAX_TASKS                 = 100
MAX_DEPENDENCIES_PER_TASK = 20
MAX_FACTS                 = 200
MAX_INFERENCES            = 100
MAX_RISKS                 = 100
MAX_PLAN_SIZE_BYTES       = 1 * 1024 * 1024   # 1 MB
MAX_CONSTRAINTS           = 50


# ------------------------------------------------------------------
# Request
# ------------------------------------------------------------------

class PlanningRequest(BaseModel):
    request_id:      str
    workspace_id:    str
    objective:       str = Field(..., min_length=1)
    constraints:     List[str] = Field(default_factory=list)
    requested_mode:  PlanningMode = PlanningMode.ANALYZE
    language:        str = "auto"
    conversation_id: Optional[str] = None

    @field_validator("objective")
    @classmethod
    def validate_objective_length(cls, v: str) -> str:
        if len(v) > MAX_OBJECTIVE_LENGTH:
            raise ValueError(f"Objective exceeds maximum length of {MAX_OBJECTIVE_LENGTH} characters.")
        return v

    @field_validator("constraints")
    @classmethod
    def validate_constraints_count(cls, v: List[str]) -> List[str]:
        if len(v) > MAX_CONSTRAINTS:
            raise ValueError(f"Too many constraints (max {MAX_CONSTRAINTS}).")
        return v


# ------------------------------------------------------------------
# Task
# ------------------------------------------------------------------

class PlanningTask(BaseModel):
    task_id:              str
    title:                str
    description:          str
    task_type:            TaskType
    dependencies:         List[str] = Field(default_factory=list)
    required_tools:       List[str] = Field(default_factory=list)
    estimated_complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    risk_level:           RiskLevel = RiskLevel.LOW
    status:               TaskStatus = TaskStatus.PENDING

    @field_validator("dependencies")
    @classmethod
    def validate_dep_count(cls, v: List[str]) -> List[str]:
        if len(v) > MAX_DEPENDENCIES_PER_TASK:
            raise ValueError(f"Too many dependencies per task (max {MAX_DEPENDENCIES_PER_TASK}).")
        return v


# ------------------------------------------------------------------
# Risk record
# ------------------------------------------------------------------

class RiskRecord(BaseModel):
    risk_id:     str
    level:       RiskLevel
    description: str
    category:    str
    impact:      str
    blocked:     bool = False


# ------------------------------------------------------------------
# Permission analysis record
# ------------------------------------------------------------------

class PermissionAnalysis(BaseModel):
    permission: str
    status:     PermissionRequirement
    reason:     str


# ------------------------------------------------------------------
# Result
# ------------------------------------------------------------------

class PlanningResult(BaseModel):
    plan_id:              str
    workspace_id:         str
    conversation_id:      Optional[str] = None
    objective:            str
    mode:                 PlanningMode
    summary:              str
    assumptions:          List[str] = Field(default_factory=list)
    facts:                List[str] = Field(default_factory=list)
    inferences:           List[str] = Field(default_factory=list)
    tasks:                List[PlanningTask] = Field(default_factory=list)
    dependency_graph:     Dict[str, List[str]] = Field(default_factory=dict)
    risks:                List[RiskRecord] = Field(default_factory=list)
    required_permissions: List[PermissionAnalysis] = Field(default_factory=list)
    blocked_actions:      List[str] = Field(default_factory=list)
    verification_plan:    List[str] = Field(default_factory=list)
    confidence:           float = Field(default=0.5, ge=0.0, le=1.0)
    status:               str = "COMPLETE"
    created_at:           str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    request_id:           Optional[str] = None
    duration_ms:          Optional[float] = None

    class Config:
        use_enum_values = True
