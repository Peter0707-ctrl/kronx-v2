"""
Phase 4.3 — Question Coverage & Output Fidelity Evaluator
Validates that the final response directly and comprehensively answers the user's
specific question, respects format/detail constraints, preserves language matching,
and avoids unrelated topics.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from intelligence.schemas import TaskContract, DomainType, IntentType


class QuestionCoverageEvaluator:
    """Evaluates answer directness, question coverage, detail level, and language fidelity."""

    SWAHILI_STOPWORDS = {
        "kwa", "katika", "yake", "kama", "hili", "hiyo", "yote", "wote", "nini", "gani",
        "eleza", "toa", "jinsi", "ya", "wa", "na", "ni", "za", "la", "cha", "vya", "vipi",
        "tafadhali", "nisaidie", "kuhusu", "kwenye", "ndani", "kiswahili", "kiingereza", "lugha"
    }
    ENGLISH_STOPWORDS = {
        "what", "how", "why", "who", "when", "where", "explain", "describe", "analyze",
        "the", "and", "from", "with", "this", "that", "there", "image", "picture", "photo",
        "photograph", "screenshot", "file", "document", "read", "extract", "using", "inside",
        "show", "tell", "give", "teach", "step", "steps", "brief", "short", "sentence",
        "only", "about", "for", "are", "can", "you", "does", "did", "have", "has", "had",
        "which", "would", "could", "should", "will", "your", "my", "our", "their", "its",
        "english", "swahili", "language"
    }


    @classmethod
    def evaluate(
        cls,
        contract: TaskContract,
        answer: str,
        expected_detail: str = "STANDARD",
        expected_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Evaluates the generated response against the task contract and user constraints.
        """
        reasons: List[str] = []
        clean_q = contract.user_goal.strip()
        ans_clean = answer.strip()

        # 1. Non-empty check
        if not ans_clean:
            return {
                "passed": False,
                "coverage_score": 0.0,
                "detail_match": False,
                "language_match": False,
                "unrelated_topics_present": False,
                "should_regenerate": True,
                "reasons": ["Empty response generated."],
            }

        # 2. Detail Level Check
        detail_match = True
        sentences = [s.strip() for s in re.split(r'[\.\!\?]\s+', ans_clean) if s.strip()]

        if expected_detail == "BRIEF" or "one sentence" in clean_q.lower() or "kwa sentensi moja" in clean_q.lower():
            if len(sentences) > 3 and len(ans_clean.split()) > 60:
                detail_match = False
                reasons.append("Response is too long for requested brief/one-sentence constraint.")

        elif expected_detail == "STEP_BY_STEP" or "step by step" in clean_q.lower() or "hatua kwa hatua" in clean_q.lower():
            has_steps = bool(re.search(r'(?:^|\n)\s*(?:\d+[\.\)]|\-|\*|Step\s*\d+)', ans_clean, re.IGNORECASE))
            if not has_steps and len(sentences) > 1:
                detail_match = False
                reasons.append("Response lacks explicit step-by-step numbering.")

        # 3. Language Match Check
        language_match = True
        swahili_triggers = ["kwa kiswahili", "eleza kwa kiswahili", "fafanua kwa kiswahili", "tafadhali", "nini maana ya", "usanisinuru"]
        wants_swahili = expected_language == "sw" or any(t in clean_q.lower() for t in swahili_triggers)

        if wants_swahili:
            sw_markers = ["ni", "ya", "wa", "kwa", "katika", "hiki", "hili", "huu", "utafiti", "mbinu", "mfumo", "sababu", "maana", "hatua", "usanisinuru", "mimea"]
            ans_low = ans_clean.lower()
            sw_count = sum(1 for m in sw_markers if re.search(r'\b' + m + r'\b', ans_low))
            if sw_count < 1 and len(ans_clean.split()) > 10:
                language_match = False
                reasons.append("Response does not appear to be in requested Swahili language.")

        # 4. Unrelated Topics Check (Domain Contamination)
        unrelated_topics = False
        if contract.domain in [DomainType.ACADEMIC, DomainType.RESEARCH, DomainType.SOFTWARE, DomainType.MATHEMATICS, DomainType.SCIENCE]:
            forex_leak_words = ["forex", "eurusd", "mt5", "pips", "leverage", "stop loss", "broker", "candlestick"]
            q_low = clean_q.lower()
            if not any(fw in q_low for fw in forex_leak_words):
                if any(fw in ans_clean.lower() for fw in forex_leak_words):
                    unrelated_topics = True
                    reasons.append("Unrelated Forex/trading terms leaked into non-financial response.")

        # 5. Calculate Overall Coverage Score
        q_words = {
            w for w in re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', clean_q.lower())
            if w not in cls.ENGLISH_STOPWORDS and w not in cls.SWAHILI_STOPWORDS
        }

        if q_words:
            ans_words = set(re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', ans_clean.lower()))
            overlap = q_words.intersection(ans_words)
            keyword_coverage = len(overlap) / float(len(q_words)) if q_words else 1.0
        else:
            keyword_coverage = 1.0

        # Adjust score based on checks
        coverage_score = keyword_coverage
        if not detail_match:
            coverage_score *= 0.8
        if not language_match:
            coverage_score *= 0.5
        if unrelated_topics:
            coverage_score *= 0.1

        passed = (
            coverage_score >= 0.2 and
            detail_match and
            language_match and
            not unrelated_topics
        )

        return {
            "passed": passed,
            "coverage_score": round(coverage_score, 3),
            "detail_match": detail_match,
            "language_match": language_match,
            "unrelated_topics_present": unrelated_topics,
            "should_regenerate": not passed,
            "reasons": reasons,
        }
