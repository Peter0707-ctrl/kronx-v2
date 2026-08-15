"""
Phase 2I.1 — Multimodal Provider Abstraction & Adapters
Pluggable, server-controlled provider interface with strict error sanitization and no key exposure.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import base64
import uuid
from datetime import datetime, timezone

from multimodal.schemas import (
    ImageGenerationRequest,
    ImageGenerationResult,
)
from multimodal.errors import (
    MultimodalError,
    CAPABILITY_UNAVAILABLE,
    PROVIDER_ERROR,
)
from multimodal.sanitizer import redact_secrets, detect_prompt_injection


class MultimodalProvider(ABC):
    """Abstract interface for multimodal vision, OCR, document, and image generation providers."""

    @abstractmethod
    def analyze_text(self, prompt: str, content: str) -> Dict[str, Any]:
        """Analyze text-based file contents."""
        pass

    @abstractmethod
    def analyze_image(self, image_bytes: bytes, mime_type: str, prompt: str) -> Dict[str, Any]:
        """Analyze image or screenshot content."""
        pass

    @abstractmethod
    def analyze_document(self, doc_bytes: bytes, mime_type: str, filename: str) -> Dict[str, Any]:
        """Analyze document structure and contents."""
        pass

    @abstractmethod
    def extract_ocr(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract text from image using OCR."""
        pass

    @abstractmethod
    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate creative image artifact."""
        pass


class MockMultimodalProvider(MultimodalProvider):
    """
    Deterministic, offline, safe provider implementation.
    Used for unit testing, offline environments, and fallback handling.
    Strictly returns verifiable metadata or explicit NOT_FOUND / UNCERTAIN.
    """

    def analyze_text(self, prompt: str, content: str) -> Dict[str, Any]:
        sanitized = redact_secrets(content)
        warnings = detect_prompt_injection(content)
        line_count = len(content.splitlines()) if content else 0
        word_count = len(content.split()) if content else 0

        return {
            "description": f"Analyzed text content ({line_count} lines, {word_count} words).",
            "summary": f"Content summary: {sanitized[:200]}..." if len(sanitized) > 200 else sanitized,
            "facts": [f"Document contains {line_count} lines of text.", f"Word count is {word_count} words."],
            "inferences": [],
            "assumptions": [],
            "warnings": warnings,
        }

    def analyze_image(self, image_bytes: bytes, mime_type: str, prompt: str) -> Dict[str, Any]:
        size_kb = len(image_bytes) / 1024
        warnings = detect_prompt_injection(prompt)

        return {
            "image_type": mime_type.split("/")[-1].upper() if "/" in mime_type else "IMAGE",
            "dimensions": {"width": 0, "height": 0},
            "description": f"Visual asset ({size_kb:.1f} KB, {mime_type}).",
            "ui_elements": [],
            "diagram_nodes": [],
            "visible_text": "",
            "visual_summary": "Image received for processing.",
            "facts": [
                f"Image format is {mime_type}.",
                f"Image size is {size_kb:.1f} KB.",
            ],
            "inferences": [],
            "assumptions": [],
            "warnings": warnings,
        }

    def analyze_document(self, doc_bytes: bytes, mime_type: str, filename: str) -> Dict[str, Any]:
        size_kb = len(doc_bytes) / 1024
        text_content = ""
        try:
            text_content = doc_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""

        sanitized = redact_secrets(text_content)
        warnings = detect_prompt_injection(sanitized)

        return {
            "document_type": filename.split(".")[-1].upper() if "." in filename else "DOCUMENT",
            "page_count": 1 if sanitized else 0,
            "sections": [{"title": "Document Content", "level": 1, "content": sanitized[:500], "page": 1}] if sanitized else [],
            "tables": [],
            "metadata": {"filename": filename, "size_kb": f"{size_kb:.1f}"},
            "text_preview": sanitized[:200] if sanitized else "",
            "word_count": len(sanitized.split()) if sanitized else 0,
            "facts": [
                f"Document '{filename}' processed ({size_kb:.1f} KB).",
            ],
            "inferences": [],
            "assumptions": [],
            "warnings": warnings,
        }

    def extract_ocr(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        return {
            "extracted_text": "",
            "word_count": 0,
            "confidence": 0.0,
            "blocks": [],
            "warnings": ["OCR requires active optical vision provider."],
        }




    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        warnings = detect_prompt_injection(request.prompt)
        artifact_id = f"art_img_{uuid.uuid4().hex[:10]}"

        # Deterministic lightweight SVG/Base64 placeholder data
        mock_svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{request.width}" height="{request.height}" viewBox="0 0 {request.width} {request.height}">'
            f'<rect width="100%" height="100%" fill="#0a0a0f"/>'
            f'<circle cx="{request.width//2}" cy="{request.height//2}" r="{min(request.width, request.height)//3}" fill="#3b82f6" opacity="0.8"/>'
            f'<text x="50%" y="50%" fill="#ffffff" font-size="24" font-family="sans-serif" text-anchor="middle" dy=".3em">{request.category.upper()}: {request.prompt[:30]}</text>'
            f'</svg>'
        )
        b64_data = base64.b64encode(mock_svg.encode("utf-8")).decode("utf-8")

        return ImageGenerationResult(
            artifact_id=artifact_id,
            format="svg+xml",
            prompt=redact_secrets(request.prompt),
            description=f"Generated {request.style} visual asset for category '{request.category}'.",
            media_type="image/svg+xml",
            b64_data=b64_data,
            artifact_url=f"/api/multimodal/artifacts/{artifact_id}",
            dimensions={"width": request.width, "height": request.height},
            style=request.style,
            category=request.category,
            status="GENERATED",
            warnings=warnings,
        )


class ProviderRegistry:
    """Server-side registry for multimodal provider instances."""

    _providers: Dict[str, MultimodalProvider] = {
        "mock": MockMultimodalProvider(),
        "default": MockMultimodalProvider(),
    }
    _active_provider_name: str = "default"

    @classmethod
    def get_provider(cls, name: Optional[str] = None) -> MultimodalProvider:
        prov_name = name or cls._active_provider_name
        if prov_name not in cls._providers:
            raise MultimodalError(
                CAPABILITY_UNAVAILABLE,
                f"Requested multimodal provider '{prov_name}' is not available."
            )
        return cls._providers[prov_name]

    @classmethod
    def register_provider(cls, name: str, provider: MultimodalProvider) -> None:
        cls._providers[name] = provider

    @classmethod
    def set_active_provider(cls, name: str) -> None:
        if name not in cls._providers:
            raise MultimodalError(
                CAPABILITY_UNAVAILABLE,
                f"Provider '{name}' cannot be set as active because it is not registered."
            )
        cls._active_provider_name = name
