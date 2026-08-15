"""
Phase 4.1 — Image & OCR Grounding Engine
Enforces strict 5-state visual provenance classification (OBSERVED, OCR_DETECTED, INFERRED, UNCERTAIN, NOT_FOUND),
visual-text verification against OCR tokens, and prompt injection defense.
"""
from __future__ import annotations
import re
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
    def verify_visual_text_claims(
        cls,
        claimed_text: str,
        ocr_result: Optional[OCRResultData],
    ) -> Tuple[bool, ObservationProvenance, str]:
        """
        Validates whether a specific text string claimed to be in the image is supported by OCR evidence.
        """
        if not ocr_result or not ocr_result.extracted_text.strip():
            return False, ObservationProvenance.NOT_FOUND, "No text was detected in the provided image."

        if ocr_result.uncertain:
            return False, ObservationProvenance.UNCERTAIN, "The visible text is blurry or of low optical clarity."

        c_low = claimed_text.lower().strip()
        ocr_low = ocr_result.extracted_text.lower()

        if c_low in ocr_low:
            return True, ObservationProvenance.OCR_DETECTED, f"Text verified from OCR: '{claimed_text}'"

        # Check token-level overlap
        c_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]+\b', c_low))
        ocr_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]+\b', ocr_low))

        if c_tokens and c_tokens.issubset(ocr_tokens):
            return True, ObservationProvenance.OCR_DETECTED, f"Token match verified from OCR: '{claimed_text}'"

        return False, ObservationProvenance.NOT_FOUND, f"Text '{claimed_text}' was not detected in the image OCR output."

    @classmethod
    def formulate_image_answer(
        cls,
        query: str,
        filename: str,
        ocr_result: Optional[OCRResultData],
        visual_elements: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[VisualEvidence]]:
        """
        Formulates a grounded visual analysis answer distinguishing observed facts from inferences and missing objects.
        """
        evidences: List[VisualEvidence] = []
        query_low = query.lower()

        has_text = ocr_result and bool(ocr_result.extracted_text.strip())
        elements_list = visual_elements or []

        # 1. Ingest OCR Evidence
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

        # 2. Ingest Visual Elements
        for elem in elements_list:
            evidences.append(
                VisualEvidence(
                    visual_id=f"vis_{uuid.uuid4().hex[:10]}",
                    filename=filename,
                    provenance=ObservationProvenance.OBSERVED,
                    element_type=elem.get("type", "Visual Feature"),
                    description=elem.get("label", "Detected visual feature"),
                    confidence=elem.get("confidence", 0.90),
                )
            )

        # 3. Check for specific requested objects/text in query
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', query_low))
        inquiry_words = {
            "what", "where", "when", "which", "does", "explain", "describe", "show", "tell",
            "image", "picture", "photo", "this", "there", "any", "visible", "seen", "observe",
            "found", "contain", "content", "the", "title", "heading", "text", "words", "shown",
            "present", "view", "read", "logo", "screenshot", "chart", "diagram", "object",
            "objects", "item", "items", "element", "elements", "feature", "features", "thing",
            "things", "are", "can", "you", "how", "who", "all", "has", "have", "had", "was",
            "were", "been", "with", "from"
        }
        target_entities = q_tokens - inquiry_words



        # Check if user asks for specific nonexistent items (e.g., "car", "signature", "submarine", "person")
        if target_entities:
            all_observed_text = (ocr_result.extracted_text.lower() if has_text else "") + " " + " ".join(e.get("label", "").lower() for e in elements_list)
            missing = [t for t in target_entities if t not in all_observed_text]

            # If user explicitly asks about specific missing items and no OCR/elements match
            if missing and len(missing) == len(target_entities) and not any(k in query_low for k in ["describe", "everything", "all", "what is in", "what is", "analyze", "read", "title", "shown"]):
                ans = f"**Visual Analysis of `{filename}`:**\n\n- **[NOT FOUND]:** The requested item(s) ({', '.join(sorted(missing))}) were not found in the provided image."
                evidences.append(
                    VisualEvidence(
                        visual_id=f"vis_notfound_{uuid.uuid4().hex[:8]}",
                        filename=filename,
                        provenance=ObservationProvenance.NOT_FOUND,
                        element_type="Absent Feature",
                        description=f"Item '{', '.join(missing)}' not present in image.",
                        confidence=1.0,
                    )
                )
                return ans, evidences


        # Build Standard Grounded Analysis
        lines = [f"**Visual Analysis of `{filename}`:**\n"]

        if has_text:
            if ocr_result.uncertain:
                lines.append(f"- **[UNCERTAIN]:** The text is not sufficiently clear to determine with certainty, but partially appears to contain: *\"{ocr_result.extracted_text}\"*")
            else:
                lines.append(f"- **[OCR_DETECTED]:** Visible text detected: *\"{ocr_result.extracted_text}\"*")
        else:
            if any(w in query_low for w in ["text", "title", "read", "words", "heading", "name"]):
                lines.append("- **[NOT_FOUND]:** No legible text was detected in the provided image.")

        if elements_list:
            lines.append("- **[OBSERVED]:**")
            for elem in elements_list:
                lines.append(f"  * {elem.get('type', 'Element')}: {elem.get('label', 'Visual feature')} (Confidence: {elem.get('confidence', 0.9):.0%})")
        elif not has_text:
            lines.append("- **[OBSERVED]:** Image binary is present, but no specific labeled visual elements or legible text were detected.")

        if ocr_result and ocr_result.warning:
            lines.append(f"\n> ⚠️ *Note: {ocr_result.warning}*")

        return "\n".join(lines), evidences
