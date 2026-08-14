"""
Phase 2J — High-Level LLM Client
Client wrapper providing convenient inference and chat completion methods with bounded retries.
"""
from typing import Optional, List, Dict, Any, Iterator
import time
from llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMMessage,
    LLMRole,
    LLMCapability,
    LLMProvider,
)
from llm.errors import LLMError, PROVIDER_UNAVAILABLE, MODEL_TIMEOUT


class LLMClient:
    """High-level client for applications and agent modules to call the LLM Gateway."""

    def __init__(self, orchestrator):
        self._orchestrator = orchestrator

    def complete(
        self,
        prompt: str,
        tenant_id: str = "default_tenant",
        user_id: str = "system",
        model: Optional[str] = None,
        capabilities: Optional[List[LLMCapability]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        dry_run: bool = False,
    ) -> LLMResponse:
        req = LLMRequest(
            tenant_id=tenant_id,
            user_id=user_id,
            model=model,
            messages=[LLMMessage(role=LLMRole.USER, content=prompt)],
            requested_capabilities=capabilities or [LLMCapability.TEXT],
            max_tokens=max_tokens,
            temperature=temperature,
            dry_run=dry_run,
        )
        return self._orchestrator.execute(req)

    def stream(
        self,
        prompt: str,
        tenant_id: str = "default_tenant",
        user_id: str = "system",
        model: Optional[str] = None,
    ) -> Iterator[str]:
        req = LLMRequest(
            tenant_id=tenant_id,
            user_id=user_id,
            model=model,
            messages=[LLMMessage(role=LLMRole.USER, content=prompt)],
            stream=True,
        )
        return self._orchestrator.stream(req)
