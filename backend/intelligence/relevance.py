"""
Phase 4.0 — Context & Memory Relevance Filter
Server-side gate evaluating historical memory and conversation items against the current task contract to eliminate topic contamination.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from intelligence.schemas import TaskContract, DomainType


class ContextRelevanceFilter:
    """Filters conversation history and memory vault items to eliminate topic contamination."""

    @staticmethod
    def _extract_keywords(text: str) -> set[str]:
        """Extracts significant keywords (length >= 3, lowercase)."""
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "you", "are", "have",
            "what", "how", "why", "who", "when", "where", "can", "will", "about", "your",
            "kwa", "katika", "yake", "kama", "hili", "hiyo", "yote", "wote", "nini", "gani"
        }
        tokens = re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', text.lower())
        return {t for t in tokens if t not in stop_words}

    @classmethod
    def calculate_relevance_score(cls, current_query: str, item_text: str, domain: DomainType) -> float:
        """
        Calculates relevance score between 0.0 and 1.0.
        Penalizes severe domain clashes (e.g., Forex keywords inside an Academic/Science task).
        """
        if not current_query or not item_text:
            return 0.0

        q_kw = cls._extract_keywords(current_query)
        item_kw = cls._extract_keywords(item_text)

        if not q_kw or not item_kw:
            return 0.0

        overlap = q_kw.intersection(item_kw)
        jaccard = len(overlap) / float(len(q_kw.union(item_kw)))

        # Domain Conflict Detection
        forex_keywords = {"forex", "trading", "mt5", "eurusd", "gbpusd", "crypto", "bitcoin", "candlestick", "leverage"}
        has_forex_in_item = any(w in item_kw for w in forex_keywords)

        if domain in [DomainType.ACADEMIC, DomainType.RESEARCH, DomainType.SOFTWARE, DomainType.MATHEMATICS]:
            if has_forex_in_item and not any(w in q_kw for w in forex_keywords):
                # Severe topic contamination penalty
                return 0.0

        # Direct term match boost
        if any(term in item_text.lower() for term in q_kw):
            jaccard += 0.25

        return min(1.0, max(0.0, jaccard))

    @classmethod
    def filter_memories(
        cls,
        contract: TaskContract,
        memories: List[Dict[str, Any]],
        threshold: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """Filters memories, keeping only those strictly relevant to the current task contract."""
        filtered = []
        for mem in memories:
            content = mem.get("content", "")
            score = cls.calculate_relevance_score(contract.user_goal, content, contract.domain)
            if score >= threshold:
                clean_mem = dict(mem)
                clean_mem["relevance_score"] = score
                filtered.append(clean_mem)
        return filtered

    @classmethod
    def filter_history(
        cls,
        contract: TaskContract,
        history: List[Dict[str, Any]],
        max_items: int = 5,
        threshold: float = 0.15,
    ) -> List[Dict[str, Any]]:
        """
        Filters recent conversation turns to exclude off-topic context.
        Recent turn within same topic is preserved; radical topic shifts drop older turns.
        """
        if not history:
            return []

        relevant_history = []
        for turn in history[-max_items:]:
            content = turn.get("content", "")
            # Always check if turn has heavy domain clash
            score = cls.calculate_relevance_score(contract.user_goal, content, contract.domain)
            
            # If previous turn was a completely different topic (e.g. Forex vs Thesis), drop it
            if score >= threshold or len(relevant_history) > 0:
                relevant_history.append(turn)

        return relevant_history
