"""
Phase 4.2 — Comprehensive Intent, Domain, Capability & Modality Classifier
Enforces strict task classification, capability mapping, evidence mandates, and modality bounds.
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
        # 1. Image Generation & UI Design
        (
            re.compile(r'\b(create|generate|draw|design|make|paint|illustrate|mockup|wireframe)\b.*\b(image|picture|logo|photo|artwork|illustration|banner|poster|icon|ui|interface|dashboard)\b', re.IGNORECASE),
            IntentType.IMAGE_GENERATION,
            DomainType.CREATIVE,
            TaskType.CREATIVE_GENERATION,
            [CapabilityType.CREATIVE_GENERATION],
            False,
        ),
        # 2. Image Analysis
        (
            re.compile(r'\b(analyze|describe|what is in|what does|inspect|examine|read|look at|view|see in|show in)\b.*\b(image|picture|photo|screenshot|diagram|chart|graph|logo|visual|icon)\b', re.IGNORECASE),
            IntentType.IMAGE_ANALYSIS,
            DomainType.GENERAL,
            TaskType.IMAGE_ANALYSIS,
            [CapabilityType.VISION, CapabilityType.OCR],
            True,
        ),
        # 3. OCR
        (
            re.compile(r'\b(extract text|ocr|read text|transcribe|read handwriting|detect text)\b', re.IGNORECASE),
            IntentType.OCR,
            DomainType.GENERAL,
            TaskType.OCR,
            [CapabilityType.OCR, CapabilityType.DOCUMENT_ANALYSIS],
            True,
        ),
        # 4. Multi-Document Comparison
        (
            re.compile(r'\b(compare|contrast|difference between|cross-examine|matrix)\b.*\b(documents|papers|files|theses|pdfs|studies)\b', re.IGNORECASE),
            IntentType.MULTI_DOCUMENT_ANALYSIS,
            DomainType.RESEARCH,
            TaskType.COMPARISON,
            [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # 5. Forex & Crypto Trading
        (
            re.compile(r'\b(forex|trading|mt5|mt4|eurusd|gbpusd|usdjpy|candlestick|leverage|lot size|stop loss|take profit|pips|crypto|bitcoin|scalping)\b', re.IGNORECASE),
            IntentType.FOREX,
            DomainType.FOREX,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 6. Academic & Research Thesis / Methodology
        (
            re.compile(r'\b(methodology|research gap|problem statement|conceptual framework|theoretical framework|literature review|sampling technique|sample size|hypotheses|dissertation|thesis|journal paper|msc|phd|research design|data collection|qualitative|quantitative|academic|apa citation|research objective|research question|formulate.*objective|objective)\b', re.IGNORECASE),
            IntentType.ACADEMIC,
            DomainType.ACADEMIC,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING, CapabilityType.LONG_CONTEXT],
            False,
        ),

        # 7. Document Analysis
        (
            re.compile(r'\b(analyze|summarize|explain|review|check|extract from)\b.*\b(pdf|document|docx|file|chapter|report|paper|thesis)\b', re.IGNORECASE),
            IntentType.DOCUMENT_ANALYSIS,
            DomainType.ACADEMIC,
            TaskType.DOCUMENT_ANALYSIS,
            [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # 8. Code Debugging
        (
            re.compile(r'\b(debug|fix error|traceback|syntaxerror|exception|typeerror|segmentation fault|panic|stacktrace|bug)\b', re.IGNORECASE),
            IntentType.CODE_DEBUGGING,
            DomainType.SOFTWARE,
            TaskType.CODE_REASONING,
            [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # 9. Code Generation / Software Engineering
        (
            re.compile(r'\b(write|create|implement|build|code|script|program|function|class|algorithm)\b.*\b(python|javascript|typescript|c\+\+|rust|golang|sql|react|fastapi|html|css)\b', re.IGNORECASE),
            IntentType.CODE_GENERATION,
            DomainType.SOFTWARE,
            TaskType.CODE_REASONING,
            [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # 10. General Coding fallback
        (
            re.compile(r'\b(python|javascript|typescript|c\+\+|rust|golang|sql|function|class|algorithm|compile|code)\b', re.IGNORECASE),
            IntentType.CODING,
            DomainType.SOFTWARE,
            TaskType.CODE_REASONING,
            [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # 11. Mathematics
        (
            re.compile(r'\b(calculate|integral|derivative|matrix|algebra|geometry|theorem|equation|solve|pythagorean|math|arithmetic|eigenvalue|calculus)\b', re.IGNORECASE),
            IntentType.MATHEMATICS,
            DomainType.MATHEMATICS,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.MATHEMATICAL_REASONING, CapabilityType.TEXT_REASONING],
            False,
        ),
        # 12. Science (Physics, Biology, Chemistry)
        (
            re.compile(r'\b(photosynthesis|mitochondria|dna|rna|quantum|relativity|thermodynamics|newton|gravity|chemistry|biology|physics|molecule|cellular|ecosystem)\b', re.IGNORECASE),
            IntentType.SCIENCE,
            DomainType.SCIENCE,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 13. Data Analysis
        (
            re.compile(r'\b(csv|dataframe|excel|spreadsheet|statistics|mean|median|std dev|correlation|regression|data analysis)\b', re.IGNORECASE),
            IntentType.DATA_ANALYSIS,
            DomainType.RESEARCH,
            TaskType.DATA_ANALYSIS,
            [CapabilityType.DATA_ANALYSIS, CapabilityType.TEXT_REASONING],
            True,
        ),
        # 14. Business & Finance
        (
            re.compile(r'\b(finance|brela|tra|tax|tzs|shilingi|budget|business plan|marketing strategy|revenue|roi|balance sheet)\b', re.IGNORECASE),
            IntentType.BUSINESS,
            DomainType.BUSINESS,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 15. Translation
        (
            re.compile(r'\b(translate|tafsiri|swahili to english|english to swahili|kwa kiswahili|kwa kiingereza)\b', re.IGNORECASE),
            IntentType.TRANSLATION,
            DomainType.GENERAL,
            TaskType.QUESTION_ANSWERING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 16. Summarization
        (
            re.compile(r'\b(summarize|kwa ufupi|summary|taja kwa muhtasari|brief overview|key points)\b', re.IGNORECASE),
            IntentType.SUMMARIZATION,
            DomainType.GENERAL,
            TaskType.SUMMARIZATION,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 17. Tutoring / Step-by-Step Explanation
        (
            re.compile(r'\b(teach me|step by step|explain how|nifundishe|kwa nini|how does it work|tutorial)\b', re.IGNORECASE),
            IntentType.TUTORING,
            DomainType.ACADEMIC,
            TaskType.TUTORING,
            [CapabilityType.TEXT_REASONING],
            False,
        ),
        # 18. Creative Writing
        (
            re.compile(r'\b(write a story|creative story|poem|fiction|creative writing|novel|tale|essay|poetry)\b', re.IGNORECASE),
            IntentType.CREATIVE_WRITING,
            DomainType.CREATIVE,
            TaskType.CREATIVE_GENERATION,
            [CapabilityType.CREATIVE_GENERATION],
            False,
        ),
    ]

    @classmethod
    def classify(
        cls,
        message: str,
        has_files: bool = False,
        has_images: bool = False,
        file_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Classifies incoming query into fine-grained intent, domain, task type,
        required capabilities, external knowledge permissions, and evidence requirement.
        """
        clean_msg = message.strip()
        clean = clean_msg

        # Multi-document check if multiple files are provided
        if has_files and file_count > 1:
            return {
                "primary_intent": IntentType.MULTI_DOCUMENT_ANALYSIS,
                "domain": DomainType.RESEARCH,
                "task_type": TaskType.COMPARISON,
                "required_capabilities": [CapabilityType.LONG_CONTEXT, CapabilityType.DOCUMENT_ANALYSIS],
                "external_knowledge_allowed": False,
                "evidence_required": True,
            }



        msg_low = clean_msg.lower()


        # Image analysis takes priority when an image is attached or explicitly inquired
        if has_images or any(k in msg_low for k in ["this image", "the photo", "in the picture", "this screenshot", "image show"]):
            if any(k in msg_low for k in ["extract text", "ocr", "read text", "words in image"]):
                return {
                    "primary_intent": IntentType.OCR,
                    "domain": DomainType.GENERAL,
                    "task_type": TaskType.OCR,
                    "required_capabilities": [CapabilityType.VISION, CapabilityType.OCR],
                    "evidence_required": True,
                    "modality": "IMAGE",
                    "external_knowledge_allowed": False,
                    "evidence_mandatory": True,
                }
            return {
                "primary_intent": IntentType.IMAGE_ANALYSIS,
                "domain": DomainType.GENERAL,
                "task_type": TaskType.IMAGE_ANALYSIS,
                "required_capabilities": [CapabilityType.VISION, CapabilityType.OCR],
                "evidence_required": True,
                "modality": "IMAGE",
                "external_knowledge_allowed": False,
                "evidence_mandatory": True,
            }

        # Multi-document comparison check
        if has_files and any(k in msg_low for k in ["compare", "difference", "contrast", "both documents", "all files"]):
            return {
                "primary_intent": IntentType.MULTI_DOCUMENT_ANALYSIS,
                "domain": DomainType.RESEARCH,
                "task_type": TaskType.COMPARISON,
                "required_capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
                "evidence_required": True,
                "modality": "DOCUMENT",
                "external_knowledge_allowed": False,
                "evidence_mandatory": True,
            }

        # Document analysis when files are attached
        if has_files:
            return {
                "primary_intent": IntentType.DOCUMENT_ANALYSIS,
                "domain": DomainType.RESEARCH,
                "task_type": TaskType.DOCUMENT_ANALYSIS,
                "required_capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
                "evidence_required": True,
                "modality": "DOCUMENT",
                "external_knowledge_allowed": False,
                "evidence_mandatory": True,
            }

        # Scan deterministic regex patterns
        for pattern, intent, domain, task, caps, ev_req in cls._INTENT_PATTERNS:
            if pattern.search(clean_msg):
                return {
                    "primary_intent": intent,
                    "domain": domain,
                    "task_type": task,
                    "required_capabilities": caps,
                    "evidence_required": ev_req,
                    "modality": "TEXT",
                    "external_knowledge_allowed": True,
                    "evidence_mandatory": ev_req,
                }

        # Default fallback: General QA / General Knowledge
        return {
            "primary_intent": IntentType.GENERAL_QA,
            "domain": DomainType.GENERAL,
            "task_type": TaskType.QUESTION_ANSWERING,
            "required_capabilities": [CapabilityType.TEXT_REASONING],
            "evidence_required": False,
            "modality": "TEXT",
            "external_knowledge_allowed": True,
            "evidence_mandatory": False,
        }
