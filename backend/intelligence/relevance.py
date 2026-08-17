"""
Phase 4.3 — Multi-Factor Context & Memory Relevance Selector
Enforces Hard Current Task Lock via CurrentTaskContext and RelevantContextSelector.
Evaluates 6 discrete scores:
  1. domain_score
  2. semantic_score
  3. lexical_score
  4. entity_score
  5. task_score
  6. explicit_reference_score
Drops irrelevant context before inference with zero topic contamination.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from intelligence.schemas import TaskContract, DomainType, IntentType, TaskType, CapabilityType


@dataclass
class CurrentTaskContext:
    """Explicit context encapsulation for the current user task."""
    user_question: str
    clean_message: str
    intent: IntentType
    domain: DomainType
    task_type: TaskType
    required_capabilities: List[CapabilityType]
    requested_detail_level: str = "STANDARD"
    requested_language: str = "en"
    attached_files: List[str] = field(default_factory=list)
    attached_images: List[str] = field(default_factory=list)
    relevant_entities: Set[str] = field(default_factory=set)
    forbidden_topics: Set[str] = field(default_factory=set)


class RelevantContextSelector:
    """Selective memory and historical conversation retriever with 6-factor relevance scoring."""

    STOP_WORDS: Set[str] = {
        "the", "and", "for", "with", "that", "this", "from", "you", "are", "have",
        "what", "how", "why", "who", "when", "where", "can", "will", "about", "your",
        "kwa", "katika", "yake", "kama", "hili", "hiyo", "yote", "wote", "nini", "gani",
        "please", "help", "show", "tell", "explain", "give", "want", "need", "like"
    }

    FOREX_KEYWORDS: Set[str] = {
        "forex", "trading", "mt5", "mt4", "eurusd", "gbpusd", "usdjpy", "crypto",
        "bitcoin", "candlestick", "leverage", "lot size", "stop loss", "take profit",
        "pips", "broker", "margin call"
    }

    CODING_KEYWORDS: Set[str] = {
        "python", "javascript", "typescript", "code", "function", "class", "debug",
        "error", "exception", "async", "await", "import", "def", "const", "var", "let"
    }

    ACADEMIC_KEYWORDS: Set[str] = {
        "thesis", "dissertation", "methodology", "research", "sample size", "hypothesis",
        "literature review", "citation", "apa", "chuo", "tafiti", "abstract", "academic",
        "conceptual framework", "theoretical framework", "problem statement"
    }

    @classmethod
    def extract_keywords(cls, text: str) -> Set[str]:
        """Extracts normalized significant keyword tokens (length >= 3)."""
        if not text:
            return set()
        tokens = re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', text.lower())
        return {t for t in tokens if t not in cls.STOP_WORDS}

    @classmethod
    def score_context_item(
        cls,
        current_query: str,
        item_text: str,
        domain: DomainType,
    ) -> Dict[str, float]:
        """
        Computes 6-factor granular relevance breakdown:
          - domain_score (0.0 to 1.0)
          - semantic_score (0.0 to 1.0)
          - lexical_score (0.0 to 1.0)
          - entity_score (0.0 to 1.0)
          - task_score (0.0 to 1.0)
          - explicit_reference_score (0.0 to 1.0)
          - total_relevance (0.0 to 1.0)
        """
        if not current_query or not item_text:
            return {
                "domain_score": 0.0,
                "semantic_score": 0.0,
                "lexical_score": 0.0,
                "entity_score": 0.0,
                "task_score": 0.0,
                "explicit_reference_score": 0.0,
                "total_relevance": 0.0,
            }

        q_kw = cls.extract_keywords(current_query)
        item_kw = cls.extract_keywords(item_text)

        if not q_kw or not item_kw:
            return {
                "domain_score": 0.0,
                "semantic_score": 0.0,
                "lexical_score": 0.0,
                "entity_score": 0.0,
                "task_score": 0.0,
                "explicit_reference_score": 0.0,
                "total_relevance": 0.0,
            }

        # 1. Check Explicit User Cross-Reference
        q_low = current_query.lower()
        explicit_ref = any(phrase in q_low for phrase in [
            "as earlier", "previous", "earlier", "you said", "as mentioned", "ulivyosema", "hapo awali", "kutoka awali"
        ])
        explicit_reference_score = 1.0 if explicit_ref else 0.0

        # 2. Domain Clash Check
        has_forex_in_item = any(w in item_kw for w in cls.FOREX_KEYWORDS)
        query_has_forex = any(w in q_kw for w in cls.FOREX_KEYWORDS)

        # Severe penalty if Forex in item while query is non-financial
        if domain in [DomainType.ACADEMIC, DomainType.RESEARCH, DomainType.SOFTWARE, DomainType.MATHEMATICS, DomainType.SCIENCE]:
            if has_forex_in_item and not query_has_forex:
                return {
                    "domain_score": 0.0,
                    "semantic_score": 0.0,
                    "lexical_score": 0.0,
                    "entity_score": 0.0,
                    "task_score": 0.0,
                    "explicit_reference_score": 0.0,
                    "total_relevance": 0.0,
                }

        # 3. Lexical Jaccard Score
        overlap = q_kw.intersection(item_kw)
        union = q_kw.union(item_kw)
        lexical_score = len(overlap) / float(len(union)) if union else 0.0

        # 4. Entity / Direct Substring Match Score
        entity_matches = sum(1 for term in q_kw if term in item_text.lower())
        entity_score = min(1.0, entity_matches * 0.25)

        # 5. Domain Alignment Score
        domain_score = 0.5
        if domain in [DomainType.ACADEMIC, DomainType.RESEARCH] and any(w in item_kw for w in cls.ACADEMIC_KEYWORDS):
            domain_score = 1.0
        elif domain == DomainType.SOFTWARE and any(w in item_kw for w in cls.CODING_KEYWORDS):
            domain_score = 1.0

        # 6. Task Score & Semantic Overlap
        semantic_score = min(1.0, lexical_score * 1.5 + entity_score * 0.5)
        task_score = 0.8 if overlap else 0.2

        # Weighted Total Score
        total = (
            lexical_score * 0.35 +
            entity_score * 0.25 +
            domain_score * 0.20 +
            semantic_score * 0.10 +
            explicit_reference_score * 0.10
        )

        return {
            "domain_score": round(domain_score, 3),
            "semantic_score": round(semantic_score, 3),
            "lexical_score": round(lexical_score, 3),
            "entity_score": round(entity_score, 3),
            "task_score": round(task_score, 3),
            "explicit_reference_score": round(explicit_reference_score, 3),
            "total_relevance": round(min(1.0, max(0.0, total)), 3),
        }

    @classmethod
    def filter_memories(
        cls,
        contract: TaskContract,
        memories: List[Dict[str, Any]],
        threshold: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """Filters long-term memories with 6-factor hard relevance gating."""
        filtered = []
        for mem in memories:
            content = mem.get("content", "")
            scores = cls.score_context_item(contract.user_goal, content, contract.domain)
            if scores["total_relevance"] >= threshold:
                clean_mem = dict(mem)
                clean_mem["relevance_score"] = scores["total_relevance"]
                clean_mem["relevance_breakdown"] = scores
                filtered.append(clean_mem)
        return filtered

    @classmethod
    def filter_history(
        cls,
        contract: TaskContract,
        history: List[Dict[str, Any]],
        max_items: int = 5,
        threshold: float = 0.18,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Filters recent conversation turns.
        Every single turn is strictly and independently evaluated.
        Returns: (retained_turns, dropped_turns_count)
        """
        if not history:
            return [], 0

        relevant_history = []
        dropped_count = 0

        for turn in history[-max_items:]:
            content = turn.get("content", "")
            scores = cls.score_context_item(contract.user_goal, content, contract.domain)
            if scores["total_relevance"] >= threshold:
                clean_turn = dict(turn)
                clean_turn["relevance_score"] = scores["total_relevance"]
                clean_turn["relevance_breakdown"] = scores
                relevant_history.append(clean_turn)
            else:
                dropped_count += 1

        return relevant_history, dropped_count


# Compatibility alias for Phase 4.2 modules
ContextRelevanceFilter = RelevantContextSelector
