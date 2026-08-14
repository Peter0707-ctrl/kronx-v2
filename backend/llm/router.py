"""
Phase 2J — LLM Model Router
Deterministic capability-based routing across providers and models.
"""
from typing import Optional, List
from llm.schemas import (
    LLMProvider,
    LLMCapability,
    LLMRequest,
    LLMRouteDecision,
)
from llm.capabilities import ModelCapabilityRegistry
from llm.errors import LLMError, MODEL_NOT_FOUND, CAPABILITY_UNSUPPORTED


def _to_str(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


class ModelRouter:
    """Routes LLM requests to suitable models and providers based on required capabilities."""

    def __init__(self, registry: Optional[ModelCapabilityRegistry] = None):
        self.registry = registry or ModelCapabilityRegistry()

    def route(self, request: LLMRequest) -> LLMRouteDecision:
        """Determines the appropriate provider and model for an inference request."""
        caps = request.requested_capabilities or [LLMCapability.TEXT]

        # Case 1: Specific model requested by user/client
        if request.model:
            model_info = self.registry.get_model(request.model)
            if not model_info or not model_info.is_active:
                raise LLMError(
                    MODEL_NOT_FOUND,
                    f"Requested model '{request.model}' is not registered or active.",
                )

            if not self.registry.supports_capabilities(request.model, caps):
                raise LLMError(
                    CAPABILITY_UNSUPPORTED,
                    f"Model '{request.model}' does not support requested capabilities: {[_to_str(c) for c in caps]}",
                )

            return LLMRouteDecision(
                provider=model_info.provider,
                model=model_info.id,
                matched_capabilities=caps,
                reason=f"Direct model match for '{request.model}'.",
            )

        # Case 2: Specific provider requested
        if request.provider:
            matched_model = self.registry.find_best_model(caps, preferred_provider=request.provider)
            if not matched_model:
                raise LLMError(
                    CAPABILITY_UNSUPPORTED,
                    f"Provider '{_to_str(request.provider)}' has no available model supporting capabilities: {[_to_str(c) for c in caps]}",
                )
            return LLMRouteDecision(
                provider=matched_model.provider,
                model=matched_model.id,
                matched_capabilities=caps,
                reason=f"Matched best model '{matched_model.id}' under provider '{_to_str(request.provider)}'.",
            )

        # Case 3: Automatic Capability-based Selection
        best_model = self.registry.find_best_model(caps)
        if not best_model:
            raise LLMError(
                CAPABILITY_UNSUPPORTED,
                f"No registered model supports the requested capabilities: {[_to_str(c) for c in caps]}",
            )

        return LLMRouteDecision(
            provider=best_model.provider,
            model=best_model.id,
            matched_capabilities=caps,
            reason=f"Automatically routed to '{best_model.id}' for capabilities {[_to_str(c) for c in caps]}.",
        )

