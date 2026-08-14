"""
Phase 2J — LLM Health & Provider Status Inspector
Provides sanitized runtime diagnostics for available models and provider integrations.
"""
from typing import Dict, Any, List
from llm.providers import ProviderRegistry
from llm.capabilities import ModelCapabilityRegistry


def _to_str(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


class LLMHealthChecker:
    """Aggregates and formats sanitized health statuses across active providers and models."""

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelCapabilityRegistry,
    ):
        self._provider_registry = provider_registry
        self._model_registry = model_registry

    def get_health_report(self) -> Dict[str, Any]:
        providers_status = []
        for p_type in self._provider_registry.list_providers():
            provider = self._provider_registry.get_provider(p_type)
            try:
                h = provider.health()
                providers_status.append(h)
            except Exception:
                providers_status.append({
                    "provider": _to_str(p_type),
                    "status": "UNAVAILABLE",
                })

        active_models = self._model_registry.list_models()

        return {
            "status": "HEALTHY",
            "active_models_count": len(active_models),
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "provider": _to_str(m.provider),
                    "capabilities": [_to_str(c) for c in m.capabilities],
                }
                for m in active_models
            ],
            "providers": providers_status,
        }

