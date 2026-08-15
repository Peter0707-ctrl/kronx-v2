"""
Phase 4.1 — 10-Point Response Quality Gate
Authoritative multi-factor validator evaluating every draft response before client return.
Triggers bounded auto-regeneration (up to 2 attempts) or transparent limitation returns on persistent failure.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from intelligence.schemas import (
    TaskContract, EvidenceItem, ClaimItem, ClaimStatus,
    IntentType, DomainType, ObservationProvenance
)


class CheckResult(BaseModel):
    check_name: str
    status: str  # PASS, FAIL, NOT_APPLICABLE
    reason: str


class QualityGateResult(BaseModel):
    passed: bool
    score: float = 1.0  # 0.0 to 1.0
    checks: List[CheckResult] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    should_regenerate: bool = False


class QualityGate:
    """10-Point Quality Gate ensuring evidence grounding, intent matching, and topic fidelity."""

    _UNRELATED_DOMAINS = {
        "forex_trading": {"forex", "trading", "mt5", "meta trader", "eurusd", "gbpusd", "candlestick", "leverage", "stop loss"},
        "crypto": {"bitcoin", "ethereum", "crypto", "blockchain", "solana"},
    }

    _FABRICATED_MOCK_STRINGS = [
        "kron-x enterprise architecture engine",
        "zero trust security layer",
        "multi-tenant workspaces",
        "navigation bar",
        "authentication input",
    ]

    @classmethod
    def evaluate(
        cls,
        contract: TaskContract,
        answer_text: str,
        evidence_pool: List[EvidenceItem],
        claims: List[ClaimItem],
    ) -> QualityGateResult:
        """Evaluates draft answer against all 10 quality checks."""
        checks: List[CheckResult] = []
        failures: List[str] = []
        ans_low = answer_text.lower()
        q_low = contract.user_goal.lower()

        # 1. Intent Match Check
        intent_pass = True
        if contract.intent == IntentType.IMAGE_GENERATION and "visual analysis" in ans_low:
            intent_pass = False
            failures.append("Task is IMAGE_GENERATION but output contains IMAGE_ANALYSIS.")
        elif contract.intent in [IntentType.IMAGE_ANALYSIS, IntentType.OCR] and "generated image" in ans_low:
            intent_pass = False
            failures.append("Task is IMAGE_ANALYSIS but output contains generative claims.")

        checks.append(CheckResult(
            check_name="IntentMatch",
            status="PASS" if intent_pass else "FAIL",
            reason="Aligned with classified intent." if intent_pass else failures[-1],
        ))

        # 2. Topic Match Check (Domain Contamination / Forex)
        topic_pass = True
        for domain_name, kw_set in cls._UNRELATED_DOMAINS.items():
            user_has = any(w in q_low for w in kw_set)
            if not user_has:
                ans_matches = [w for w in kw_set if w in ans_low]
                if len(ans_matches) >= 2:
                    topic_pass = False
                    failures.append(f"Unrelated domain contamination detected: {domain_name}")
                    break

        checks.append(CheckResult(
            check_name="TopicMatch",
            status="PASS" if topic_pass else "FAIL",
            reason="Response strictly stays within requested topic." if topic_pass else failures[-1],
        ))

        # 3. Evidence Match Check
        ev_pass = True
        if contract.evidence_required and not evidence_pool and contract.intent not in [IntentType.IMAGE_ANALYSIS, IntentType.OCR]:
            if "not stated" not in ans_low and "not found" not in ans_low and "unable to verify" not in ans_low:
                ev_pass = False
                failures.append("Evidence required but no evidence provided and no explicit missing disclaimer present.")

        checks.append(CheckResult(
            check_name="EvidenceSupport",
            status="PASS" if ev_pass else "FAIL",
            reason="Evidence available or explicitly qualified." if ev_pass else failures[-1],
        ))


        # 4. Claim Support Check
        unsupported = [c for c in claims if c.status == ClaimStatus.UNSUPPORTED]
        claim_pass = len(unsupported) == 0 if contract.evidence_required else True
        if not claim_pass:
            failures.append(f"Contains {len(unsupported)} unsupported claims.")

        checks.append(CheckResult(
            check_name="ClaimSupport",
            status="PASS" if claim_pass else "FAIL",
            reason="All factual claims are supported or qualified." if claim_pass else failures[-1],
        ))

        # 5. Source Fidelity Check
        source_pass = True
        if evidence_pool:
            valid_sources = {e.provenance.source_file.lower() for e in evidence_pool}
            # Check if answer cites fake files
            cited_files = re.findall(r'`([^`]+\.(?:txt|pdf|docx|csv|json|py|js|ts|go))`', ans_low)
            for cf in cited_files:
                if cf not in valid_sources and not any(vs in cf for vs in valid_sources):
                    source_pass = False
                    failures.append(f"Answer cited nonexistent source file '{cf}'.")
                    break

        checks.append(CheckResult(
            check_name="SourceFidelity",
            status="PASS" if source_pass else "FAIL",
            reason="All citations match verified uploaded files." if source_pass else failures[-1],
        ))

        # 6. Language Match Check
        lang_pass = True
        if contract.language == "sw":
            sw_words = {"katika", "utafiti", "mbinu", "malengo", "kwa", "yake", "hili", "muundo", "maelezo"}
            has_sw = any(w in ans_low for w in sw_words)
            if not has_sw and len(ans_low.split()) > 15:
                lang_pass = False
                failures.append("Requested Swahili language but response is purely English.")

        checks.append(CheckResult(
            check_name="LanguageMatch",
            status="PASS" if lang_pass else "FAIL",
            reason="Response language matches request." if lang_pass else failures[-1],
        ))

        # 7. Completeness Check
        comp_pass = len(answer_text.strip()) > 0
        checks.append(CheckResult(
            check_name="Completeness",
            status="PASS" if comp_pass else "FAIL",
            reason="Response content generated." if comp_pass else "Response is empty.",
        ))

        # 8. Uncertainty Correctness Check
        uncertain_pass = True
        if any("blur" in q_low or "unclear" in q_low or "low optical" in q_low for _ in [1]):
            if "uncertain" not in ans_low and "unclear" not in ans_low and "could not" not in ans_low:
                uncertain_pass = False
                failures.append("Blurry/unclear input did not produce uncertainty qualification.")

        checks.append(CheckResult(
            check_name="UncertaintyCorrectness",
            status="PASS" if uncertain_pass else "FAIL",
            reason="Uncertainty acknowledged where appropriate." if uncertain_pass else failures[-1],
        ))

        # 9. Hallucination Check (Mock Strings)
        hallucination_pass = True
        for mock_str in cls._FABRICATED_MOCK_STRINGS:
            if mock_str in ans_low and mock_str not in q_low:
                hallucination_pass = False
                failures.append(f"Detected fabricated mock template string: '{mock_str}'")
                break

        checks.append(CheckResult(
            check_name="HallucinationCheck",
            status="PASS" if hallucination_pass else "FAIL",
            reason="Zero fabricated mock strings detected." if hallucination_pass else failures[-1],
        ))

        # 10. User Question Coverage
        coverage_pass = True
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9_-]{4,}\b', q_low))
        stop_tokens = {
            "what", "when", "where", "which", "does", "explain", "analyze", "describe", "please",
            "could", "would", "compare", "comparison", "methodology", "methodologies", "both",
            "papers", "files", "documents", "document", "study", "studies", "summarize", "check",
            "tell", "show", "give", "find"
        }
        core_tokens = q_tokens - stop_tokens

        if core_tokens and len(ans_low.split()) > 30 and contract.intent != IntentType.MULTI_DOCUMENT_ANALYSIS:
            overlap = [t for t in core_tokens if t in ans_low]
            if not overlap and "not stated" not in ans_low and "not found" not in ans_low:
                coverage_pass = False
                failures.append("Draft answer does not mention any core keywords from the user prompt.")

        checks.append(CheckResult(
            check_name="UserQuestionCoverage",
            status="PASS" if coverage_pass else "FAIL",
            reason="Directly addresses user question." if coverage_pass else failures[-1],
        ))


        passed_count = sum(1 for c in checks if c.status == "PASS")
        total_count = len(checks)
        score = passed_count / float(total_count)
        overall_pass = len(failures) == 0

        return QualityGateResult(
            passed=overall_pass,
            score=score,
            checks=checks,
            reasons=failures,
            should_regenerate=not overall_pass,
        )
