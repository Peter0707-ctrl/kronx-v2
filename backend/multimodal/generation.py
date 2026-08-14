"""
Phase 2I.1 — Multimodal Creative Generation Engine
Generates images, logos, diagrams, and UI mockups in-memory without unconstrained filesystem write access.
"""
import uuid
from typing import Dict, Any, List, Optional
from multimodal.schemas import (
    ImageGenerationRequest,
    ImageGenerationResult,
    DesignGenerationRequest,
    DesignGenerationResult,
)
from multimodal.providers import ProviderRegistry
from multimodal.sanitizer import redact_secrets, detect_prompt_injection
from multimodal.limits import MAX_IMAGE_DIMENSION
from multimodal.errors import MultimodalError, INVALID_REQUEST


class CreativeGenerationEngine:
    """Safely coordinates creative image generation and structured design synthesis."""

    def generate_image(
        self,
        request: ImageGenerationRequest,
        provider_name: Optional[str] = None,
    ) -> ImageGenerationResult:
        """Generates an image artifact using the registered provider."""
        if not request.prompt or not request.prompt.strip():
            raise MultimodalError(INVALID_REQUEST, "Generation prompt cannot be empty.")

        if request.width > MAX_IMAGE_DIMENSION or request.height > MAX_IMAGE_DIMENSION:
            raise MultimodalError(
                INVALID_REQUEST,
                f"Image dimensions ({request.width}x{request.height}) exceed maximum allowed dimension ({MAX_IMAGE_DIMENSION}px)."
            )

        sanitized_prompt = redact_secrets(request.prompt)
        warnings = detect_prompt_injection(request.prompt)

        provider = ProviderRegistry.get_provider(provider_name)
        result = provider.generate_image(request)
        if warnings:
            result.warnings.extend(warnings)
            result.warnings = list(dict.fromkeys(result.warnings))

        return result

    def generate_design(
        self,
        request: DesignGenerationRequest,
    ) -> DesignGenerationResult:
        """Synthesizes structured design and UI mockup specifications."""
        if not request.title or not request.title.strip():
            raise MultimodalError(INVALID_REQUEST, "Design title cannot be empty.")

        sanitized_prompt = redact_secrets(request.prompt)
        warnings = detect_prompt_injection(request.prompt)

        design_id = f"des_{uuid.uuid4().hex[:10]}"

        # Standard clean modern design system tokens
        default_palette = request.color_palette or ["#0f172a", "#1e293b", "#3b82f6", "#10b981", "#f8fafc"]
        components = request.components or ["Navbar", "HeroSection", "FeatureGrid", "CallToAction", "Footer"]

        structured_design = {
            "title": request.title,
            "design_type": request.design_type,
            "style_system": request.style_system or "modern_clean",
            "typography": {
                "font_family": "Inter, system-ui, sans-serif",
                "heading_scale": [32, 24, 20, 16],
            },
            "layout": {
                "container_max_width": "1200px",
                "grid_columns": 12,
                "spacing_unit": 8,
            },
            "color_palette": default_palette,
        }

        mockup_metadata = {
            "responsive_breakpoints": ["640px", "768px", "1024px", "1280px"],
            "component_count": len(components),
            "theme": "dark_mode_optimized",
        }

        visual_components = [
            {"id": f"comp_{idx+1}", "name": comp, "role": "LayoutBlock", "render_order": idx+1}
            for idx, comp in enumerate(components)
        ]

        return DesignGenerationResult(
            design_id=design_id,
            title=request.title,
            design_type=request.design_type,
            structured_design=structured_design,
            mockup_metadata=mockup_metadata,
            visual_components=visual_components,
            warnings=warnings,
        )
