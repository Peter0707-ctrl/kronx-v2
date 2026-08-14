"""
Phase 2I — AI Agent Brain Schemas & Models
Strict Pydantic models for agent requests, intents, context, decisions, results, and decision traces.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    ANALYZE          = "ANALYZE"
    EXPLAIN          = "EXPLAIN"
    DEBUG            = "DEBUG"
    DESIGN           = "DESIGN"
    REFACTOR         = "REFACTOR"
    REVIEW           = "REVIEW"
    DOCUMENT         = "DOCUMENT"
    MODIFY           = "MODIFY"
    VERIFY           = "VERIFY"
    ANALYZE_IMAGE    = "ANALYZE_IMAGE"
    ANALYZE_DOCUMENT = "ANALYZE_DOCUMENT"
    GENERATE_IMAGE   = "GENERATE_IMAGE"
    UNKNOWN          = "UNKNOWN"



class RiskLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class ReasoningMode(str, Enum):
    ANALYZE  = "ANALYZE"
    REFINE   = "REFINE"
    OPTIMIZE = "OPTIMIZE"
    DOCUMENT = "DOCUMENT"
    DRY_RUN  = "DRY_RUN"
    MODIFY   = "MODIFY"
    VERIFY   = "VERIFY"


class AgentStatus(str, Enum):
    IDLE                = "IDLE"
    RUNNING             = "RUNNING"
    AWAITING_PERMISSION = "AWAITING_PERMISSION"
    COMPLETED           = "COMPLETED"
    FAILED              = "FAILED"
    CANCELLED           = "CANCELLED"


# ------------------------------------------------------------------
# Request & Intent Models
# ------------------------------------------------------------------

class AgentRequest(BaseModel):
    request_id:      str = Field(default_factory=lambda: f"agtreq_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    workspace_id:    str
    objective:       str
    conversation_id: Optional[str] = None
    mode:            ReasoningMode = ReasoningMode.ANALYZE
    language:        Optional[str] = "python"
    constraints:     List[str] = Field(default_factory=list)
    dry_run:         bool = True
    metadata:        Dict[str, Any] = Field(default_factory=dict)


class AgentIntent(BaseModel):
    intent_type:            IntentType
    confidence:             float
    normalized_objective:   str
    requested_capabilities: List[str] = Field(default_factory=list)
    risk_level:             RiskLevel = RiskLevel.LOW


# ------------------------------------------------------------------
# Context & Decision Models
# ------------------------------------------------------------------

class AgentContext(BaseModel):
    workspace_id:        str
    tenant_id:           str
    user_id:             str
    project_profile:     Dict[str, Any] = Field(default_factory=dict)
    relevant_files:      List[str] = Field(default_factory=list)
    relevant_facts:      List[str] = Field(default_factory=list)
    relevant_inferences: List[str] = Field(default_factory=list)
    assumptions:         List[str] = Field(default_factory=list)
    constraints:         List[str] = Field(default_factory=list)


class AgentDecision(BaseModel):
    decision_id:           str
    request_id:            str
    intent:                AgentIntent
    reasoning_mode:        ReasoningMode
    selected_plan_id:      Optional[str] = None
    requested_permissions: List[str] = Field(default_factory=list)
    allowed_actions:       List[str] = Field(default_factory=list)
    blocked_actions:       List[str] = Field(default_factory=list)
    next_step:             str
    confidence:            float
    risk_level:            RiskLevel


# ------------------------------------------------------------------
# Result & Trace Models
# ------------------------------------------------------------------

class AgentResult(BaseModel):
    agent_id:            str
    request_id:          str
    status:              AgentStatus
    summary:             str
    decision:            Optional[AgentDecision] = None
    plan_id:             Optional[str] = None
    execution_id:        Optional[str] = None
    modification_id:     Optional[str] = None
    verification_id:     Optional[str] = None
    blocked_actions:     List[str] = Field(default_factory=list)
    warnings:            List[str] = Field(default_factory=list)
    trace_id:            str = ""
    created_at:          str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))


class DecisionTrace(BaseModel):
    trace_id:               str
    request_id:             str
    tenant_id:              str
    user_id:                str
    workspace_id:           str
    intent:                 str
    risk:                   str
    requested_capabilities: List[str] = Field(default_factory=list)
    policy_decisions:       Dict[str, str] = Field(default_factory=dict)
    selected_plan:          Optional[str] = None
    execution_reference:    Optional[str] = None
    modification_reference: Optional[str] = None
    verification_reference: Optional[str] = None
    final_decision:         str = ""
    duration_ms:            float = 0.0
    created_at:             str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
