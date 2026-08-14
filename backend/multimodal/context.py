"""
Phase 2I.1 — Multimodal Context Integrator
Integrates multimodal intelligence observations into Phase 2I Agent Brain context structures.
"""
from typing import List, Dict, Any, Tuple, Optional
from multimodal.schemas import (

    FileAnalysisResult,
    DocumentAnalysisResult,
    ImageAnalysisResult,
    OCRResult,
    ImageGenerationResult,
    DesignGenerationResult,
)
from multimodal.limits import MAX_MULTIMODAL_CONTEXT_ITEMS
from multimodal.sanitizer import redact_secrets


class MultimodalContextIntegrator:
    """
    Transforms multimodal analysis results into structured facts, inferences, and assumptions
    for consumption by the Phase 2I Agent Brain.
    """

    def integrate_findings(
        self,
        file_res: Optional[FileAnalysisResult] = None,
        doc_res: Optional[DocumentAnalysisResult] = None,
        img_res: Optional[ImageAnalysisResult] = None,
        ocr_res: Optional[OCRResult] = None,
        gen_res: Optional[ImageGenerationResult] = None,
        des_res: Optional[DesignGenerationResult] = None,
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Combines and bounds multimodal observations into (facts, inferences, assumptions).
        """
        facts: List[str] = []
        inferences: List[str] = []
        assumptions: List[str] = []

        if file_res:
            facts.extend(file_res.facts)
            inferences.extend(file_res.inferences)
            assumptions.extend(file_res.assumptions)

        if doc_res:
            facts.extend(doc_res.facts)
            inferences.extend(doc_res.inferences)
            assumptions.extend(doc_res.assumptions)

        if img_res:
            facts.extend(img_res.facts)
            inferences.extend(img_res.inferences)
            assumptions.extend(img_res.assumptions)

        if ocr_res:
            facts.append(f"OCR extracted {ocr_res.word_count} words with {int(ocr_res.confidence * 100)}% confidence.")
            inferences.append("Image contains textual content suitable for search and semantic indexing.")
            assumptions.append("Extracted OCR text represents passive visible typography.")

        if gen_res:
            facts.append(f"Generated {gen_res.style} visual asset '{gen_res.artifact_id}' ({gen_res.category}).")
            inferences.append("Visual asset is ready for client preview.")
            assumptions.append("Asset generation satisfied user design criteria.")

        if des_res:
            facts.append(f"Synthesized design specification '{des_res.title}' ({des_res.design_type}).")
            inferences.append("UI layout components are ready for frontend scaffolding.")
            assumptions.append("Color palette and responsive grid match project styling guidelines.")

        # Redact secrets and deduplicate
        sanitized_facts = [redact_secrets(f) for f in dict.fromkeys(facts)]
        sanitized_inferences = [redact_secrets(i) for i in dict.fromkeys(inferences)]
        sanitized_assumptions = [redact_secrets(a) for a in dict.fromkeys(assumptions)]

        # Enforce maximum 50 context items per category
        return (
            sanitized_facts[:MAX_MULTIMODAL_CONTEXT_ITEMS],
            sanitized_inferences[:MAX_MULTIMODAL_CONTEXT_ITEMS],
            sanitized_assumptions[:MAX_MULTIMODAL_CONTEXT_ITEMS],
        )
