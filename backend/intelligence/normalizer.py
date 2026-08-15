"""
Phase 4.0 — Request Normalization Engine
Deterministically inspects and structures incoming intelligence requests, modalities, language, and constraints.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from intelligence.schemas import IntelligenceRequest


class RequestNormalizer:
    """Normalizes raw user prompts, parameters, and input modalities."""

    @staticmethod
    def detect_language(text: str) -> str:
        """Detects whether prompt is Swahili, English, or Mixed."""
        t_low = text.lower()
        sw_words = {
            "habari", "mambo", "shule", "chuo", "tafiti", "mada", "mafunzo",
            "jinsi", "eleza", "toa", "kwa", "nini", "gani", "wapi", "lini",
            "mwalimu", "maswali", "majibu", "uhakiki", "mbinu", "nadharia",
            "takwimu", "uchambuzi", "taarifa", "picha", "faili", "biashara",
            "kazi", "tafadhali", "nisaidie", "kiswahili", "shilingi", "tzs"
        }
        en_words = {
            "what", "how", "why", "where", "when", "explain", "analyze", "describe",
            "compare", "summarize", "research", "methodology", "thesis", "study",
            "hypothesis", "sampling", "results", "discussion", "conclusion", "image",
            "document", "file", "code", "python", "debug", "create", "generate"
        }

        tokens = set(re.findall(r'\b\w+\b', t_low))
        sw_count = len(tokens.intersection(sw_words))
        en_count = len(tokens.intersection(en_words))

        if sw_count > 0 and en_count > 0:
            return "mixed"
        if sw_count > en_count and sw_count > 0:
            return "sw"
        return "en"

    @staticmethod
    def extract_requested_detail_level(text: str) -> str:
        t_low = text.lower()
        if any(w in t_low for w in ["step by step", "hatua kwa hatua", "in depth", "detailed", "kwa kina", "comprehensive", "full analysis"]):
            return "DETAILED"
        if any(w in t_low for w in ["brief", "short", "kwa ufupi", "summary", "quick", "one sentence"]):
            return "CONCISE"
        return "STANDARD"

    @classmethod
    def normalize(cls, req: IntelligenceRequest) -> Dict[str, Any]:
        """Normalizes request parameters and extracts structural goals."""
        clean_msg = req.message.strip()
        lang = req.language or cls.detect_language(clean_msg)
        detail_level = cls.extract_requested_detail_level(clean_msg)

        has_files = len(req.files) > 0
        has_images = len(req.images) > 0

        # Check for explicit questions vs directives
        is_question = "?" in clean_msg or any(clean_msg.lower().startswith(w) for w in ["what", "who", "why", "how", "when", "where", "is", "does", "nini", "wapi", "vipi", "kwanini", "je"])

        return {
            "clean_message": clean_msg,
            "language": lang,
            "detail_level": detail_level,
            "has_files": has_files,
            "has_images": has_images,
            "file_count": len(req.files),
            "image_count": len(req.images),
            "is_question": is_question,
            "constraints": req.constraints,
            "conversation_id": req.conversation_id,
            "workspace_id": req.workspace_id,
        }
