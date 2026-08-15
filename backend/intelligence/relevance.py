"""
Phase 4.2 — Multi-Factor Context & Memory Relevance Gate
Enforces Hard Current Task Lock. Evaluates domain relevance, semantic relevance,
lexical overlap, entity match, and task compatibility. Drops irrelevant context before inference.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from intelligence.schemas import TaskContract, DomainType



class ContextRelevanceFilter:
    """Hard Current Task Lock & Multi-Factor Relevance Gate for memory and conversation history."""

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
        "literature review", "citation", "apa", "chuo", "tafiti", "abstract", "academic"
    }

    @classmethod
    def extract_keywords(cls, text: str) -> Set[str]:
        """Extracts normalized significant keyword tokens (length >= 3)."""
        if not text:
            return set()
        tokens = re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', text.lower())
        return {t for t in tokens if t not in cls.STOP_WORDS}

    @classmethod
    def calculate_relevance_score(
        cls,
        current_query: str,
        item_text: str,
        domain: DomainType
    ) -> float:
        """
        Calculates multi-factor relevance score between 0.0 and 1.0.
        Factors:
          1. Lexical Jaccard overlap
          2. Direct entity / keyword substring match
          3. Domain conflict penalty (e.g. Forex in Academic/Software/Science tasks)
          4. Explicit user cross-reference check
        """
        if not current_query or not item_text:
            return 0.0

        q_kw = cls.extract_keywords(current_query)
        item_kw = cls.extract_keywords(item_text)

        if not q_kw or not item_kw:
            return 0.0

        # Check explicit reference (e.g., "as mentioned earlier", "the previous code", "the last author")
        q_low = current_query.lower()
        explicit_ref = any(phrase in q_low for phrase in [
            "as earlier", "previous", "earlier", "you said", "as mentioned", "ulivyosema", "hapo awali"
        ])

        # Domain clash check
        has_forex_in_item = any(w in item_kw for w in cls.FOREX_KEYWORDS)
        query_has_forex = any(w in q_kw for w in cls.FOREX_KEYWORDS)

        # Severe domain penalty if Forex is present in history but NOT in current Academic/Coding/Science query
        if domain in [DomainType.ACADEMIC, DomainType.RESEARCH, DomainType.SOFTWARE, DomainType.MATHEMATICS, DomainType.SCIENCE]:
            if has_forex_in_item and not query_has_forex:
                return 0.0

        # Calculate Lexical Overlap
        overlap = q_kw.intersection(item_kw)
        union = q_kw.union(item_kw)
        jaccard = len(overlap) / float(len(union)) if union else 0.0

        # Substring / Exact token matching boost
        match_count = sum(1 for term in q_kw if term in item_text.lower())
        boost = min(0.4, match_count * 0.15)

        total_score = jaccard + boost
        if explicit_ref and total_score > 0.05:
            total_score += 0.25

        return min(1.0, max(0.0, total_score))

    @classmethod
    def filter_memories(
        cls,
        contract: TaskContract,
        memories: List[Dict[str, Any]],
        threshold: float = 0.20,
    ) -> List[Dict[str, Any]]:
        """Filters long-term memories with hard relevance gating."""
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
            score = cls.calculate_relevance_score(contract.user_goal, content, contract.domain)
            if score >= threshold:
                clean_turn = dict(turn)
                clean_turn["relevance_score"] = score
                relevant_history.append(clean_turn)
            else:
                dropped_count += 1

        return relevant_history, dropped_count
