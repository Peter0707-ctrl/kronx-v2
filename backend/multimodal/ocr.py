"""
Phase 2I.1 — Multimodal OCR Engine
Extracts text from images, redacts secrets, and neutralizes prompt-injection attempts.
"""
from typing import Dict, Any, List, Optional
from multimodal.limits import check_image_size, check_ocr_text_size
from multimodal.sanitizer import redact_secrets, detect_prompt_injection
from multimodal.schemas import OCRResult, RiskLevel
from multimodal.providers import ProviderRegistry


class OCREngine:
    """Safely extracts text from images with secret redaction and prompt-injection neutralization."""

    def extract_text_from_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/png",
        provider_name: Optional[str] = None,
    ) -> OCRResult:
        """Extracts OCR text from raw image bytes."""
        check_image_size(len(image_bytes))
        provider = ProviderRegistry.get_provider(provider_name)
        raw_res = provider.extract_ocr(image_bytes, mime_type)

        raw_text = raw_res.get("extracted_text", "")
        sanitized_text = redact_secrets(raw_text)
        check_ocr_text_size(len(sanitized_text.encode("utf-8")))

        warnings = list(raw_res.get("warnings", []))
        warnings.extend(detect_prompt_injection(raw_text))
        warnings = list(dict.fromkeys(warnings))

        sanitized_blocks: List[Dict[str, Any]] = []
        for block in raw_res.get("blocks", []):
            sanitized_blocks.append({
                "text": redact_secrets(block.get("text", "")),
                "bbox": block.get("bbox", []),
                "confidence": block.get("confidence", 1.0),
            })

        risk = RiskLevel.HIGH if warnings else RiskLevel.LOW
        word_count = len(sanitized_text.split())

        return OCRResult(
            extracted_text=sanitized_text,
            word_count=word_count,
            confidence=raw_res.get("confidence", 1.0),
            blocks=sanitized_blocks,
            warnings=warnings,
            risk_level=risk,
        )
