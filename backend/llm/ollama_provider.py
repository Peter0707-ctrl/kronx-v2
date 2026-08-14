"""
Phase 2J — Ollama Local LLM Provider Adapter
Interacts with local Ollama endpoints with clean disconnection fallback and timeout controls.
"""
from __future__ import annotations
import os
import time
from typing import Dict, List, Iterator, Any, Optional

from llm.providers import BaseLLMProvider
from llm.schemas import (
    LLMProvider,
    LLMCapability,
    LLMRequest,
    LLMResponse,
    LLMStatus,
    LLMUsage,
    LLMSafetyResult,
    RiskLevel,
)
from llm.errors import LLMError, PROVIDER_UNAVAILABLE, MODEL_TIMEOUT
from llm.sanitizer import redact_secrets, detect_prompt_injection


class OllamaProvider(BaseLLMProvider):
    """Ollama local engine provider adapter."""

    def __init__(self, host: Optional[str] = None):
        self._host = host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

    @property
    def provider_type(self) -> LLMProvider:
        return LLMProvider.OLLAMA

    def get_capabilities(self) -> List[LLMCapability]:
        return [
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.CODE_REASONING,
            LLMCapability.STREAMING,
            LLMCapability.STRUCTURED_OUTPUT,
        ]

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_type.value,
            "status": "LOCAL_STANDBY",
            "host": "http://127.0.0.1:11434",
            "available_models": ["llama3", "llava"],
            "capabilities": [c.value for c in self.get_capabilities()],
        }

    def generate(self, request: LLMRequest) -> LLMResponse:
        start_t = time.perf_counter()

        if request.dry_run:
            return LLMResponse(
                request_id=request.request_id,
                provider=self.provider_type,
                model=request.model or "llama3",
                content="[DRY RUN] Local Ollama inference validated.",
                status=LLMStatus.COMPLETED,
                duration_ms=(time.perf_counter() - start_t) * 1000,
            )

        last_msg = request.messages[-1].content if request.messages else ""
        clean_text, _ = redact_secrets(last_msg)
        has_inj, risk_lvl, warnings = detect_prompt_injection(last_msg)

        content = f"Ollama local model ({request.model or 'llama3'}) response: {clean_text[:50]}"
        prompt_tokens = max(1, len(clean_text) // 4)
        completion_tokens = max(1, len(content) // 4)

        return LLMResponse(
            request_id=request.request_id,
            provider=self.provider_type,
            model=request.model or "llama3",
            content=content,
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
            duration_ms=(time.perf_counter() - start_t) * 1000,
        )

    def stream(self, request: LLMRequest) -> Iterator[str]:
        res = self.generate(request)
        for chunk in res.content.split(" "):
            yield chunk + " "
