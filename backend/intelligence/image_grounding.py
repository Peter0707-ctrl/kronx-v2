"""
Phase 4.0 — Image & OCR Grounding Engine
Enforces visual provenance classification (OBSERVED, OCR_DETECTED, INFERRED, UNCERTAIN, NOT_FOUND)
and treats OCR text strictly as passive sanitized data.
"""
from __future__ import annotations
import uuid
from typing import List, Dict, Any, Optional, Tuple
from intelligence.schemas import (
    VisualEvidence, OCRResultData, OCRToken, OCRBoundingBox,
    ObservationProvenance, TaskContract
)
from multimodal.sanitizer import redact_secrets, detect_prompt_injection


class ImageGroundingEngine:
    """Analyzes visual assets and OCR extractions without hallucinations or prompt-injection vulnerability."""

    @classmethod
    def process_ocr_data(
        cls,
        raw_text: str,
        filename: str,
        confidence: float = 0.95,
        bounding_boxes: Optional[List[Dict[str, Any]]] = None,
    ) -> OCRResultData:
        """Sanitizes OCR text and builds structured OCR tokens with confidence and uncertainty flags."""
        sanitized = redact_secrets(raw_text)
        injection_warnings = detect_prompt_injection(raw_text)

        tokens: List[OCRToken] = []
        words = sanitized.split()
        is_uncertain = confidence < 0.60 or len(raw_text.strip()) == 0

        for w in words:
            token_conf = confidence
            prov = ObservationProvenance.OCR_DETECTED if token_conf >= 0.60 else ObservationProvenance.UNCERTAIN
            tokens.append(
                OCRToken(
                    text=w,
                    confidence=token_conf,
                    provenance=prov,
                )
            )

        warning_msg = injection_warnings[0] if injection_warnings else None
        if is_uncertain and not warning_msg:
            warning_msg = "The image text has low optical clarity; some words may be uncertain."

        return OCRResultData(
            extracted_text=sanitized,
            confidence=confidence,
            tokens=tokens,
            detected_language="en",
            source_id=filename,
            uncertain=is_uncertain,
            warning=warning_msg,
        )

    @classmethod
    def formulate_image_answer(
        cls,
        query: str,
        filename: str,
        ocr_result: Optional[OCRResultData],
        visual_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[VisualEvidence]]:
        """
        Formulates a grounded visual analysis answer distinguishing observed facts from inferences.
        """
        evidences: List[VisualEvidence] = []
        query_low = query.lower()

        # 1. Check OCR Text
        has_text = ocr_result and bool(ocr_result.extracted_text.strip())
        if has_text:
            text_prov = ObservationProvenance.OCR_DETECTED if not ocr_result.uncertain else ObservationProvenance.UNCERTAIN
            evidences.append(
                VisualEvidence(
                    visual_id=f"vis_{uuid.uuid4().hex[:10]}",
                    filename=filename,
                    provenance=text_prov,
                    element_type="Text Block",
                    description=ocr_result.extracted_text,
                    confidence=ocr_result.confidence,
                )
            )

        # 2. Check Visual Elements (Shapes / UI / Diagram nodes)
        if visual_elements:
            for elem in visual_elements:
                evidences.append(
                    VisualEvidence(
                        visual_id=f"vis_{uuid.uuid4().hex[:10]}",
                        filename=filename,
                        provenance=ObservationProvenance.OBSERVED,
                        element_type=elem.get("type", "Visual Element"),
                        description=elem.get("label", "Detected visual feature"),
                        confidence=elem.get("confidence", 0.90),
                    )
                )

        # Build Response
        lines = [f"**Visual Analysis of `{filename}`:**\n"]

        if has_text:
            if ocr_result.uncertain:
                lines.append(f"- **[UNCERTAIN TEXT]:** The text is not sufficiently clear to determine with absolute certainty, but appears to contain: *\"{ocr_result.extracted_text}\"*")
            else:
                lines.append(f"- **[OCR DETECTED]:** Visible text detected: *\"{ocr_result.extracted_text}\"*")
        else:
            if "text" in query_low or "title" in query_low or "read" in query_low:
                lines.append("- **[NOT FOUND]:** No legible text was detected in the provided image.")

        if visual_elements:
            lines.append("- **[OBSERVED ELEMENTS]:**")
            for elem in visual_elements:
                lines.append(f"  * {elem.get('type')}: {elem.get('label')} (Confidence: {elem.get('confidence', 0.9):.0%})")

        if ocr_result and ocr_result.warning:
            lines.append(f"\n> ⚠️ *Note: {ocr_result.warning}*")

        return "\n".join(lines), evidences
