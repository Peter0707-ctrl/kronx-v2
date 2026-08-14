"""
Phase 2J — LLM Model Capabilities Registry
Maintains capability profiles for approved LLM providers and models.
"""
from typing import Dict, List, Optional
from llm.schemas import LLMModelInfo, LLMProvider, LLMCapability

# Default Registered Models with explicit capability mappings
REGISTERED_MODELS: Dict[str, LLMModelInfo] = {
    # Mock Provider Models (for test & offline determinism)
    "mock-text": LLMModelInfo(
        id="mock-text",
        provider=LLMProvider.MOCK,
        name="Mock Deterministic Text Engine",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.CODE_REASONING,
            LLMCapability.STRUCTURED_OUTPUT,
            LLMCapability.STREAMING,
        ],
        max_context_tokens=32000,
        max_output_tokens=4096,
        is_active=True,
    ),
    "mock-vision": LLMModelInfo(
        id="mock-vision",
        provider=LLMProvider.MOCK,
        name="Mock Vision & OCR Engine",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.OCR,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.STRUCTURED_OUTPUT,
        ],
        max_context_tokens=32000,
        max_output_tokens=4096,
        is_active=True,
    ),
    # OpenAI Models
    "gpt-4o": LLMModelInfo(
        id="gpt-4o",
        provider=LLMProvider.OPENAI,
        name="OpenAI GPT-4o Multimodal",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.OCR,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.STRUCTURED_OUTPUT,
            LLMCapability.STREAMING,
            LLMCapability.CODE_REASONING,
        ],
        max_context_tokens=128000,
        max_output_tokens=4096,
        is_active=True,
    ),
    "gpt-4o-mini": LLMModelInfo(
        id="gpt-4o-mini",
        provider=LLMProvider.OPENAI,
        name="OpenAI GPT-4o-Mini",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.STRUCTURED_OUTPUT,
            LLMCapability.STREAMING,
            LLMCapability.CODE_REASONING,
        ],
        max_context_tokens=128000,
        max_output_tokens=4096,
        is_active=True,
    ),
    # Ollama Models (Local Inference)
    "llama3": LLMModelInfo(
        id="llama3",
        provider=LLMProvider.OLLAMA,
        name="Meta Llama 3 8B Local",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.CODE_REASONING,
            LLMCapability.STRUCTURED_OUTPUT,
            LLMCapability.STREAMING,
        ],
        max_context_tokens=8192,
        max_output_tokens=2048,
        is_active=True,
    ),
    "llava": LLMModelInfo(
        id="llava",
        provider=LLMProvider.OLLAMA,
        name="LLaVA Local Vision Model",
        capabilities=[
            LLMCapability.TEXT,
            LLMCapability.VISION,
            LLMCapability.OCR,
            LLMCapability.IMAGE_ANALYSIS,
            LLMCapability.STREAMING,
        ],
        max_context_tokens=4096,
        max_output_tokens=2048,
        is_active=True,
    ),
}


class ModelCapabilityRegistry:
    """Registry providing safe lookup and capability validation for AI models."""

    def __init__(self, custom_models: Optional[Dict[str, LLMModelInfo]] = None):
        self._models: Dict[str, LLMModelInfo] = dict(REGISTERED_MODELS)
        if custom_models:
            self._models.update(custom_models)

    def get_model(self, model_id: str) -> Optional[LLMModelInfo]:
        return self._models.get(model_id)

    def list_models(self, provider: Optional[LLMProvider] = None) -> List[LLMModelInfo]:
        models = [m for m in self._models.values() if m.is_active]
        if provider:
            models = [m for m in models if m.provider == provider]
        return models

    def supports_capabilities(
        self, model_id: str, capabilities: List[LLMCapability]
    ) -> bool:
        model = self.get_model(model_id)
        if not model or not model.is_active:
            return False
        model_caps = set(model.capabilities)
        return all(cap in model_caps for cap in capabilities)

    def find_best_model(
        self,
        capabilities: List[LLMCapability],
        preferred_provider: Optional[LLMProvider] = None,
    ) -> Optional[LLMModelInfo]:
        """Finds active model satisfying all requested capabilities."""
        candidates = [m for m in self._models.values() if m.is_active]
        if preferred_provider:
            pref_matches = [
                m for m in candidates
                if m.provider == preferred_provider and self.supports_capabilities(m.id, capabilities)
            ]
            if pref_matches:
                return pref_matches[0]

        matches = [m for m in candidates if self.supports_capabilities(m.id, capabilities)]
        return matches[0] if matches else None
