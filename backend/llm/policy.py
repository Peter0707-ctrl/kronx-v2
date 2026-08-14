"""
Phase 2J — LLM Server-Side Policy Engine
Authoritative gatekeeper evaluating inference permissions, parameter bounds, and capability constraints.
"""
from typing import Optional, List
from llm.schemas import (
    LLMRequest,
    LLMCapability,
    RiskLevel,
)
from llm.errors import (
    LLMError,
    UNAUTHORIZED,
    FORBIDDEN,
    FORBIDDEN_PERMISSION_LEVEL,
    INVALID_REQUEST,
)
from llm.sanitizer import detect_prompt_injection

FORBIDDEN_PERMISSIONS = {"ADMIN", "EXECUTE", "NETWORK"}
MAX_REQUEST_MESSAGES = 100
MAX_PROMPT_CHARS = 500000


class LLMPolicyEngine:
    """Server-side policy engine enforcing identity, capability, and parameter boundaries."""

    def evaluate_request(
        self,
        request: LLMRequest,
        is_authenticated: bool = True,
        requested_permission: Optional[str] = None,
    ):
        # 1. Identity & Auth Check
        if not is_authenticated or not request.tenant_id:
            raise LLMError(
                UNAUTHORIZED,
                "Authentication required for LLM inference gateway.",
            )

        # 2. Permission escalation barrier
        if requested_permission:
            perm_upper = requested_permission.upper()
            if perm_upper in FORBIDDEN_PERMISSIONS:
                raise LLMError(
                    FORBIDDEN_PERMISSION_LEVEL,
                    f"LLM Gateway strictly blocks permission escalation to '{perm_upper}'.",
                )

        # 3. Message count and size checks
        if not request.messages or len(request.messages) == 0:
            raise LLMError(
                INVALID_REQUEST,
                "Inference request must contain at least one message.",
            )

        if len(request.messages) > MAX_REQUEST_MESSAGES:
            raise LLMError(
                INVALID_REQUEST,
                f"Inference request exceeds maximum message count ({MAX_REQUEST_MESSAGES}).",
            )

        total_chars = sum(len(m.content) for m in request.messages)
        if total_chars > MAX_PROMPT_CHARS:
            raise LLMError(
                INVALID_REQUEST,
                f"Total prompt content size ({total_chars} chars) exceeds limit ({MAX_PROMPT_CHARS} chars).",
            )

        # 4. Parameter sanity bounds
        if request.max_tokens < 1 or request.max_tokens > 16384:
            raise LLMError(
                INVALID_REQUEST,
                "max_tokens must be between 1 and 16384.",
            )

        if request.temperature < 0.0 or request.temperature > 2.0:
            raise LLMError(
                INVALID_REQUEST,
                "temperature must be between 0.0 and 2.0.",
            )
