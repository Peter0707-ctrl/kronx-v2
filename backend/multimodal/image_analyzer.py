"""
Phase 2I.1 — Multimodal Image & Vision Analyzer
Processes screenshots, diagrams, and UI assets with zero-instruction data containment.
"""
import os
import base64
from typing import Dict, Any, List, Optional
from workspace.store import WorkspaceStore
from tools.path_verify import verify_safe_path


from multimodal.file_types import classify_file_type, FileCategory
from multimodal.limits import check_image_size
from multimodal.sanitizer import redact_secrets, detect_prompt_injection
from multimodal.schemas import ImageAnalysisResult, RiskLevel
from multimodal.providers import ProviderRegistry
from multimodal.errors import (
    MultimodalError,
    FILE_NOT_FOUND,
    INVALID_REQUEST,
)


class ImageAnalyzer:
    """Safely analyzes images, screenshots, and diagrams."""

    def __init__(self, workspace_store: Optional[WorkspaceStore] = None):
        self._workspace_store = workspace_store or WorkspaceStore()

    def analyze_workspace_image(
        self,
        workspace_id: str,
        relative_path: str,
        prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> ImageAnalysisResult:
        """Analyze an image stored in an authorized workspace."""
        if not relative_path or not relative_path.strip():
            raise MultimodalError(INVALID_REQUEST, "Image path cannot be empty.")

        ws = self._workspace_store.get_workspace(workspace_id)
        if not ws:
            raise MultimodalError(INVALID_REQUEST, f"Workspace '{workspace_id}' not found.")

        ws_root = ws.get("root_path")
        if not ws_root or not os.path.exists(ws_root):
            raise MultimodalError(INVALID_REQUEST, "Workspace root does not exist on disk.")

        safe_path = verify_safe_path(ws_root, relative_path)
        if not os.path.exists(safe_path):
            raise MultimodalError(FILE_NOT_FOUND, f"Image '{relative_path}' not found.")

        size_bytes = os.path.getsize(safe_path)
        check_image_size(size_bytes)

        category, mime = classify_file_type(relative_path)
        if category != FileCategory.IMAGE:
            raise MultimodalError(INVALID_REQUEST, f"File '{relative_path}' is not an image.")

        with open(safe_path, "rb") as f:
            img_bytes = f.read(size_bytes)

        return self.analyze_image_bytes(
            image_bytes=img_bytes,
            mime_type=mime,
            prompt=prompt or "Analyze this image.",
            provider_name=provider_name,
        )

    def analyze_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        prompt: str,
        provider_name: Optional[str] = None,
    ) -> ImageAnalysisResult:
        """Analyze raw image byte payload."""
        check_image_size(len(image_bytes))
        provider = ProviderRegistry.get_provider(provider_name)
        raw_res = provider.analyze_image(image_bytes, mime_type, prompt)

        # Sanitize visible text and summaries
        visible_text = redact_secrets(raw_res.get("visible_text", ""))
        visual_summary = redact_secrets(raw_res.get("visual_summary", ""))
        description = redact_secrets(raw_res.get("description", ""))

        warnings = list(raw_res.get("warnings", []))
        warnings.extend(detect_prompt_injection(visible_text))
        warnings.extend(detect_prompt_injection(prompt))
        warnings = list(dict.fromkeys(warnings))

        facts = [redact_secrets(f) for f in raw_res.get("facts", [])]
        inferences = [redact_secrets(i) for i in raw_res.get("inferences", [])]
        assumptions = [redact_secrets(a) for a in raw_res.get("assumptions", [])]

        risk = RiskLevel.HIGH if warnings else RiskLevel.LOW

        return ImageAnalysisResult(
            image_type=raw_res.get("image_type", "IMAGE"),
            dimensions=raw_res.get("dimensions", {"width": 1024, "height": 1024}),
            description=description,
            ui_elements=raw_res.get("ui_elements", []),
            diagram_nodes=raw_res.get("diagram_nodes", []),
            visible_text=visible_text,
            visual_summary=visual_summary,
            facts=facts,
            inferences=inferences,
            assumptions=assumptions,
            warnings=warnings,
            risk_level=risk,
        )
