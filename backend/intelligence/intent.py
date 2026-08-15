"""
Phase 4.0 — Intent Classification Engine
Classifies user requests across 27+ academic, multimodal, technical, and general intents with strict current-question priority.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Tuple
from intelligence.schemas import (
    IntentType, DomainType, TaskType, CapabilityType
)


class IntentClassifier:
    """Classifies user intent, task domain, required capabilities, and evidence needs."""

    # Keywords patterns mapped to Intents
    _INTENT_PATTERNS: List[Tuple[re.Pattern, IntentType, DomainType, TaskType, List[CapabilityType], bool]] = [
        # Image Generation & UI Design
        (
            re.compile(r'\b(create|generate|draw|design|make|paint|illustrate|mockup|wireframe)\b.*\b(image|picture|logo|photo|artwork|illustration|banner|poster|icon|ui|interface|dashboard)\b', re.IGNORECASE),
            IntentType.IMAGE_GENERATION,
            DomainType.CREATIVE,
            TaskType.CREATIVE_GENERATION,
            [CapabilityType.CREATIVE_GENERATION],
            False,
        ),
        # Image Analysis
        (
            re.compile(r'\b(analyze|describe|what is in|what does|inspect|examine|read|look at|view|see in|show in)\b.*\b(image|picture|photo|screenshot|diagram|chart|graph|logo|visual|icon)\b', re.IGNORECASE),
            IntentType.IMAGE_ANALYSIS,
            DomainType.GENERAL,
            TaskType.IMAGE_ANALYSIS,
            [CapabilityType.VISION, CapabilityType.OCR],
            True,
        ),

        # OCR
        (
            re.compile(r'\b(extract text|ocr|read text|transcribe|read handwriting|detect text)\b', re.IGNORECASE),
            IntentType.OCR,
            DomainType.GENERAL,
            TaskType.OCR,
            [CapabilityType.OCR, CapabilityType.DOCUMENT_ANALYSIS],
            True,
        ),
        # Multi-Document Comparison
        (
            re.compile(r'\b(compare|contrast|difference between|cross-examine|matrix)\b.*\b(documents|papers|files|theses|pdfs|studies)\b', re.IGNORECASE),
            IntentType.MULTI_DOCUMENT_ANALYSIS,
            DomainType.RESEARCH,
            TaskType.COMPARISON,
            [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # Creative Writing
        (
            re.compile(r'\b(write a story|creative story|poem|fiction|creative writing|novel|tale|essay|poetry)\b', re.IGNORECASE),
            IntentType.CREATIVE_WRITING,
            DomainType.CREATIVE,
            TaskType.CREATIVE_GENERATION,
            [CapabilityType.CREATIVE_GENERATION],
            False,
        ),
        # Academic & Research Thesis / Methodology / Qualitative & Quantitative

        (
            re.compile(r'\b(methodology|research gap|problem statement|conceptual framework|theoretical framework|literature review|sampling technique|sample size|hypotheses|dissertation|thesis|journal paper|msc|phd|research design|data collection|qualitative|quantitative|research)\b', re.IGNORECASE),
            IntentType.ACADEMIC,
            DomainType.ACADEMIC,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING, CapabilityType.LONG_CONTEXT],
            False,
        ),

        # Document Analysis
        (
            re.compile(r'\b(analyze|summarize|explain|review|check|extract from)\b.*\b(pdf|document|docx|file|chapter|report|paper|thesis)\b', re.IGNORECASE),
            IntentType.DOCUMENT_ANALYSIS,
            DomainType.ACADEMIC,
            TaskType.DOCUMENT_ANALYSIS,
            [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # Coding & Debugging
        (
            re.compile(r'\b(debug|fix error|traceback|syntaxerror|exception|python|javascript|typescript|c\+\+|rust|function|class|algorithm|code|compile)\b', re.IGNORECASE),
            IntentType.CODING,
            DomainType.SOFTWARE,
            TaskType.CODE_REASONING,
            [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # Mathematics
        (
            re.compile(r'\b(calculate|integral|derivative|matrix|algebra|geometry|theorem|equation|solve|pythagorean|math|arithmetic)\b', re.IGNORECASE),
            IntentType.MATHEMATICS,
            DomainType.MATHEMATICS,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.MATHEMATICAL_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # Data Analysis
        (
            re.compile(r'\b(csv|dataframe|excel|spreadsheet|statistics|mean|median|std dev|correlation|regression|data analysis)\b', re.IGNORECASE),
            IntentType.DATA_ANALYSIS,
            DomainType.RESEARCH,
            TaskType.DATA_ANALYSIS,
            [CapabilityType.DATA_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # Finance & Business
        (
            re.compile(r'\b(finance|forex|currency|trading|market|investment|brela|tra|tax|tzs|shilingi|budget|business plan)\b', re.IGNORECASE),
            IntentType.FINANCE,
            DomainType.FINANCE,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # Translation
        (
            re.compile(r'\b(translate|tafsiri|translation|in english|kwa kiswahili|in swahili)\b', re.IGNORECASE),
            IntentType.TRANSLATION,
            DomainType.GENERAL,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # Summarization
        (
            re.compile(r'\b(summarize|summary|muhtasari|kwa kifupi|tldr)\b', re.IGNORECASE),
            IntentType.SUMMARIZATION,
            DomainType.GENERAL,
            TaskType.SUMMARIZATION,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
    ]

    @classmethod
    def classify(
        cls,
        message: str,
        has_files: bool = False,
        has_images: bool = False,
        file_count: int = 0,
        image_count: int = 0,
    ) -> Dict[str, Any]:
        """Classifies the primary intent based on the CURRENT user message and attachments."""
        msg = message.strip()
        msg_lower = msg.lower()

        # Attachment based heuristics
        if has_images and not any(kw in msg_lower for kw in ["create", "generate", "draw", "make a logo", "paint"]):
            if any(kw in msg_lower for kw in ["ocr", "read text", "transcribe", "extract text"]):
                return {
                    "primary_intent": IntentType.OCR,
                    "secondary_intent": IntentType.IMAGE_ANALYSIS,
                    "domain": DomainType.GENERAL,
                    "task_type": TaskType.OCR,
                    "required_capabilities": [CapabilityType.OCR, CapabilityType.VISION],
                    "evidence_required": True,
                    "confidence": 0.98,
                }
            return {
                "primary_intent": IntentType.IMAGE_ANALYSIS,
                "secondary_intent": IntentType.OCR,
                "domain": DomainType.GENERAL,
                "task_type": TaskType.IMAGE_ANALYSIS,
                "required_capabilities": [CapabilityType.VISION, CapabilityType.OCR],
                "evidence_required": True,
                "confidence": 0.95,
            }

        if has_files:
            if file_count > 1 or any(kw in msg_lower for kw in ["compare", "difference", "across these"]):
                return {
                    "primary_intent": IntentType.MULTI_DOCUMENT_ANALYSIS,
                    "secondary_intent": IntentType.ACADEMIC if "thesis" in msg_lower or "paper" in msg_lower else IntentType.DOCUMENT_ANALYSIS,
                    "domain": DomainType.RESEARCH if "thesis" in msg_lower else DomainType.GENERAL,
                    "task_type": TaskType.COMPARISON,
                    "required_capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
                    "evidence_required": True,
                    "confidence": 0.95,
                }
            return {
                "primary_intent": IntentType.DOCUMENT_ANALYSIS,
                "secondary_intent": IntentType.ACADEMIC if any(w in msg_lower for w in ["thesis", "methodology", "chapter", "research"]) else IntentType.GENERAL_QA,
                "domain": DomainType.ACADEMIC if any(w in msg_lower for w in ["thesis", "methodology", "chapter", "research"]) else DomainType.GENERAL,
                "task_type": TaskType.DOCUMENT_ANALYSIS,
                "required_capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
                "evidence_required": True,
                "confidence": 0.94,
            }

        # Pattern matching
        for pat, intent, domain, task_type, caps, ev_req in cls._INTENT_PATTERNS:
            if pat.search(msg):
                return {
                    "primary_intent": intent,
                    "secondary_intent": IntentType.GENERAL_QA,
                    "domain": domain,
                    "task_type": task_type,
                    "required_capabilities": caps,
                    "evidence_required": ev_req,
                    "confidence": 0.90,
                }

        # Default General QA / Academic Fallback
        return {
            "primary_intent": IntentType.GENERAL_QA,
            "secondary_intent": IntentType.OTHER,
            "domain": DomainType.GENERAL,
            "task_type": TaskType.QUESTION_ANSWERING,
            "required_capabilities": [CapabilityType.TEXT_REASONING],
            "evidence_required": False,
            "confidence": 0.75,
        }
