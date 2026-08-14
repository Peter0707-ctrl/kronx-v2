"""
Phase 2J — LLM Schemas & Models
Strict Pydantic models for provider abstraction, model routing, safety, budgets, quotas, and inference.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class LLMProvider(str, Enum):
    OPENAI = "OPENAI"
    OLLAMA = "OLLAMA"
    LOCAL = "LOCAL"
    CUSTOM = "CUSTOM"
    MOCK = "MOCK"


class LLMCapability(str, Enum):
    TEXT = "TEXT"
    VISION = "VISION"
    OCR = "OCR"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    STREAMING = "STREAMING"
    CODE_REASONING = "CODE_REASONING"
    EMBEDDING = "EMBEDDING"


class LLMRole(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    WORKSPACE_DATA = "workspace_data"


class LLMStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ------------------------------------------------------------------
# Core Data Models
# ------------------------------------------------------------------

class LLMMessage(BaseModel):
    role: LLMRole = LLMRole.USER
    content: str = Field(..., max_length=500000)
    name: Optional[str] = None
    raw_images: List[str] = Field(default_factory=list, description="Base64 encoded images if multimodal")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class LLMModelInfo(BaseModel):
    id: str
    provider: LLMProvider
    name: str
    capabilities: List[LLMCapability] = Field(default_factory=list)
    max_context_tokens: int = 128000
    max_output_tokens: int = 4096
    is_active: bool = True

    class Config:
        use_enum_values = True


class LLMRouteDecision(BaseModel):
    provider: LLMProvider
    model: str
    matched_capabilities: List[LLMCapability] = Field(default_factory=list)
    reason: str = ""

    class Config:
        use_enum_values = True


class LLMToolIntent(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_permission_level: str = "READ"
    confidence: float = 1.0
    is_authorized_intent: bool = False
    validation_warning: Optional[str] = None


class LLMSafetyResult(BaseModel):
    is_safe: bool = True
    risk_level: RiskLevel = RiskLevel.NONE
    violations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    redacted_secrets_count: int = 0
    prompt_injection_detected: bool = False

    class Config:
        use_enum_values = True


class LLMResponse(BaseModel):
    request_id: str
    provider: LLMProvider
    model: str
    content: str = ""
    structured_output: Optional[Dict[str, Any]] = None
    tool_intents: List[LLMToolIntent] = Field(default_factory=list)
    usage: LLMUsage = Field(default_factory=LLMUsage)
    safety: LLMSafetyResult = Field(default_factory=LLMSafetyResult)
    status: LLMStatus = LLMStatus.COMPLETED
    duration_ms: float = 0.0
    error: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    class Config:
        use_enum_values = True


class LLMRequest(BaseModel):
    request_id: str = Field(
        default_factory=lambda: f"llmreq_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}"
    )
    tenant_id: str = "default_tenant"
    user_id: str = "system"
    conversation_id: Optional[str] = None
    workspace_id: Optional[str] = None
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None
    messages: List[LLMMessage] = Field(default_factory=list)
    requested_capabilities: List[LLMCapability] = Field(default_factory=lambda: [LLMCapability.TEXT])
    max_tokens: int = Field(default=2048, ge=1, le=16384)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: float = Field(default=30.0, ge=0.0, le=120.0)
    dry_run: bool = False
    stream: bool = False


    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: List[LLMMessage]) -> List[LLMMessage]:
        if not v:
            raise ValueError("Messages list cannot be empty.")
        return v

    class Config:
        use_enum_values = True


class LLMBudget(BaseModel):
    tenant_id: str
    max_input_tokens: int = 1000000
    max_output_tokens: int = 250000
    max_cost_usd: float = 50.0
    used_input_tokens: int = 0
    used_output_tokens: int = 0
    used_cost_usd: float = 0.0


class LLMQuota(BaseModel):
    tenant_id: str
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    current_minute_count: int = 0
    current_hour_count: int = 0
    last_reset_minute: float = 0.0
    last_reset_hour: float = 0.0


class LLMInferenceRecord(BaseModel):
    request_id: str
    tenant_id: str
    user_id: str
    provider: LLMProvider
    model: str
    status: LLMStatus
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    risk_level: RiskLevel = RiskLevel.NONE
    duration_ms: float = 0.0
    error_code: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    class Config:
        use_enum_values = True
