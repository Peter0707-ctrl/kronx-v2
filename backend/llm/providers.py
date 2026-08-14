"""
Phase 2J — LLM Provider Interface & Registry
Abstract base class for inference providers and deterministic Mock provider.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Iterator, Any
import time
import json

from llm.schemas import (
    LLMProvider,
    LLMCapability,
    LLMRequest,
    LLMResponse,
    LLMStatus,
    LLMUsage,
    LLMSafetyResult,
    LLMToolIntent,
    RiskLevel,
)
from llm.errors import LLMError, PROVIDER_UNAVAILABLE, CAPABILITY_UNSUPPORTED, MODEL_NOT_FOUND
from llm.sanitizer import redact_secrets, detect_prompt_injection


class BaseLLMProvider(ABC):
    """Abstract interface for interchangeable LLM providers."""

    @property
    @abstractmethod
    def provider_type(self) -> LLMProvider:
        pass

    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Executes non-streaming completion."""
        pass

    @abstractmethod
    def stream(self, request: LLMRequest) -> Iterator[str]:
        """Yields response chunks for streaming completion."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns sanitized provider connectivity status."""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[LLMCapability]:
        """Returns list of supported capabilities."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """Deterministic, offline provider for test verification and fallback."""

    def __init__(self, name: str = "MockLLM"):
        self.name = name

    @property
    def provider_type(self) -> LLMProvider:
        return LLMProvider.MOCK

    def get_capabilities(self) -> List[LLMCapability]:
        return [
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.OCR,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.STRUCTURED_OUTPUT,
            LLMCapability.STREAMING,
            LLMCapability.CODE_REASONING,
        ]

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_type.value,
            "status": "HEALTHY",
            "available_models": ["mock-text", "mock-vision"],
            "capabilities": [c.value for c in self.get_capabilities()],
        }

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_t = time.perf_counter()
        last_msg = request.messages[-1].content if request.messages else ""

        # Dry run handling
        if request.dry_run:
            return LLMResponse(
                request_id=request.request_id,
                provider=self.provider_type,
                model=request.model or "mock-text",
                content="[DRY RUN] Inference validated with zero execution.",
                status=LLMStatus.COMPLETED,
                duration_ms=(time.perf_counter() - start_t) * 1000,
            )

        # Check prompt injection in prompt
        has_inj, risk_lvl, warnings = detect_prompt_injection(last_msg)
        clean_prompt, _ = redact_secrets(last_msg)

        # Synthesize structured response or text based on capabilities
        tool_intents = []
        structured_output = None

        if "find" in last_msg.lower() or "read" in last_msg.lower() or "inspect" in last_msg.lower():
            tool_intents.append(
                LLMToolIntent(
                    tool_name="INSPECT_FILE",
                    parameters={"path": "src/main.py"},
                    requested_permission_level="READ",
                    confidence=0.95,
                    is_authorized_intent=True,
                )
            )

        if LLMCapability.STRUCTURED_OUTPUT in request.requested_capabilities or "json" in last_msg.lower():
            structured_output = {
                "decision": "PROCEED",
                "summary": "Mock inference completed successfully.",
                "analysis": f"Evaluated input: '{clean_prompt[:50]}...'",
            }
            content = json.dumps(structured_output)
        else:
            content = f"Mock AI response for query: '{clean_prompt[:60]}' (Model: {request.model or 'mock-text'})"

        # Calculate mock token usage
        prompt_tokens = max(1, len(clean_prompt) // 4)
        completion_tokens = max(1, len(content) // 4)

        dur_ms = (time.perf_counter() - start_t) * 1000

        return LLMResponse(
            request_id=request.request_id,
            provider=self.provider_type,
            model=request.model or "mock-text",
            content=content,
            structured_output=structured_output,
            tool_intents=tool_intents,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=0.0,
            ),
            safety=LLMSafetyResult(
                is_safe=not has_inj,
                risk_level=risk_lvl,
                warnings=warnings,
                prompt_injection_detected=has_inj,
            ),
            status=LLMStatus.COMPLETED,
            duration_ms=dur_ms,
        )

    def stream(self, request: LLMRequest) -> Iterator[str]:
        response = self.generate(request)
        words = response.content.split(" ")
        for w in words:
            yield w + " "


class ProviderRegistry:
    """Manages active LLM provider adapters."""

    def __init__(self):
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {
            LLMProvider.MOCK: MockLLMProvider(),
        }

    def register(self, provider: BaseLLMProvider):
        self._providers[provider.provider_type] = provider

    def get_provider(self, provider_type: LLMProvider) -> BaseLLMProvider:
        if provider_type not in self._providers:
            # Fallback to Mock provider for safety
            return self._providers[LLMProvider.MOCK]
        return self._providers[provider_type]

    def list_providers(self) -> List[LLMProvider]:
        return list(self._providers.keys())
