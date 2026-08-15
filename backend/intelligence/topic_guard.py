"""
Phase 4.0 — Topic Guard & Question Relevance Lock
Intercepts and detects off-topic response drift, rejecting answers that deviate from the user's explicit question.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple
from intelligence.schemas import TopicDriftEvaluation, DomainType, TaskContract


class TopicGuard:
    """Hard relevance gate ensuring answer content strictly matches the user's question."""

    _UNRELATED_DOMAIN_KEYWORDS = {
        "forex_trading": {"forex", "trading", "mt5", "meta trader", "eurusd", "gbpusd", "candlestick", "leverage", "stop loss"},
        "crypto": {"bitcoin", "ethereum", "crypto", "blockchain", "solana", "altcoin"},
        "gaming": {"fortnite", "roblox", "minecraft", "playstation", "xbox"},
    }

    @classmethod
    def evaluate_drift(
        cls,
        contract: TaskContract,
        answer_text: str,
    ) -> TopicDriftEvaluation:
        """
        Evaluates whether the generated answer contains unrelated topic drift.
        """
        user_query = contract.user_goal.lower()
        ans_low = answer_text.lower()

        detected_drifts: List[str] = []

        # Check for forbidden domain injection
        for domain_name, kw_set in cls._UNRELATED_DOMAIN_KEYWORDS.items():
            # If user didn't ask about this domain, but answer mentions 2+ keywords from it
            user_has_domain = any(kw in user_query for kw in kw_set)
            if not user_has_domain:
                ans_matches = [kw for kw in kw_set if kw in ans_low]
                if len(ans_matches) >= 2:
                    detected_drifts.append(domain_name)

        if detected_drifts:
            return TopicDriftEvaluation(
                is_drifted=True,
                drift_score=0.85,
                reason=f"Detected severe topic contamination ({', '.join(detected_drifts)}) not requested in user prompt.",
                detected_unrelated_topics=detected_drifts,
            )

        # Keyword alignment check
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]{4,}\b', user_query))
        # Filter common inquiry words
        stop_tokens = {"what", "when", "where", "explain", "analyze", "describe", "please", "nini", "eleza"}
        core_q_tokens = q_tokens - stop_tokens

        if core_q_tokens:
            matches = [t for t in core_q_tokens if t in ans_low]
            match_ratio = len(matches) / float(len(core_q_tokens))
            if match_ratio < 0.15 and len(ans_low.split()) > 40:
                # Potential subtle drift
                return TopicDriftEvaluation(
                    is_drifted=False,
                    drift_score=0.35,
                    reason="Low lexical overlap with prompt, but no forbidden domain detected.",
                    detected_unrelated_topics=[],
                )

        return TopicDriftEvaluation(
            is_drifted=False,
            drift_score=0.0,
            reason="Answer is strictly aligned with user prompt.",
            detected_unrelated_topics=[],
        )
