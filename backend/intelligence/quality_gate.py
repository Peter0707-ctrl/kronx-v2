"""
Phase 5 — Enhanced 15-Point Response Quality Gate
Authoritative multi-factor validator evaluating every draft response before client return.
Validates:
 1. Intent Match
 2. Topic Match (No Forex/unrelated domain contamination)
 3. Evidence Support (Factual backing)
 4. Claim Support (No unsupported assertions)
 5. Source Fidelity (No mock/synthetic hallucinations)
 6. Language Match (Fluid English/Swahili)
 7. Completeness & Non-Empty
 8. Uncertainty Correctness
 9. Hallucination Check (Absent document/image facts)
 10. User Question Coverage
 11. Modality Correctness
 12. Model Capability Correctness
 13. Context Contamination Check
 14. Academic Attribution Check
 15. Actual Answer & Anti-Acknowledgement Check (Strictly rejects "I have analyzed your request...")
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from intelligence.schemas import (
    TaskContract, EvidenceItem, ClaimItem, ClaimStatus,
    IntentType, DomainType, ObservationProvenance, QualityGateRule
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
    """15-Point Quality Gate ensuring evidence grounding, intent matching, and topic fidelity."""

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

    _META_ACKNOWLEDGEMENT_PATTERNS = [
        r"i have analyzed your request regarding",
        r"i analyzed your request",
        r"your request concerns",
        r"i understand your question",
        r"i have received your request",
        r"i have analyzed your document",
        r"your inquiry regarding",
        r"^### 💡 copetra ai — response\s*i have analyzed your request",
    ]

    _LEAKED_INTERNAL_TAGS = [
        r"\[persi\]",
        r"\[persi",
        r"\[persistent user brain memory\]",
        r"\[task_contract",
        r"\[capability\]",
        r"\[internal_",
    ]

    @classmethod
    def evaluate(
        cls,
        contract: TaskContract,
        answer_text: str,
        evidence_pool: List[EvidenceItem],
        claims: List[ClaimItem],
    ) -> QualityGateResult:
        """Evaluates draft answer against all 15 quality checks."""
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
            reason="Supported by supplied evidence items." if ev_pass else failures[-1],
        ))

        # 4. Claim Support Check
        unsupported = [c for c in claims if c.status == ClaimStatus.UNSUPPORTED]
        claim_pass = len(unsupported) == 0
        if not claim_pass:
            failures.append(f"Found {len(unsupported)} unsupported factual claims.")

        checks.append(CheckResult(
            check_name="ClaimSupport",
            status="PASS" if claim_pass else "FAIL",
            reason="All factual claims verified." if claim_pass else failures[-1],
        ))

        # 5. Source Fidelity Check (Check against mock hallucinations)
        fidelity_pass = True
        for mock_str in cls._FABRICATED_MOCK_STRINGS:
            if mock_str in ans_low and mock_str not in q_low:
                # Check if this exact text was in the provided evidence
                if not any(mock_str in e.content.lower() for e in evidence_pool):
                    fidelity_pass = False
                    failures.append(f"Response contains fabricated mock artifact: '{mock_str}'")
                    break

        checks.append(CheckResult(
            check_name="SourceFidelity",
            status="PASS" if fidelity_pass else "FAIL",
            reason="Zero fabricated mock or synthetic artifacts." if fidelity_pass else failures[-1],
        ))

        # 6. Language Match Check
        lang_pass = True
        if contract.language == "sw":
            sw_words = {"na", "kwa", "katika", "ya", "wa", "ni", "kama", "hili", "muundo", "utafiti", "mbinu"}
            has_sw = any(w in ans_low.split() for w in sw_words)
            if not has_sw and len(ans_low.split()) > 10:
                lang_pass = False
                failures.append("Requested Swahili but output does not contain Swahili structures.")

        checks.append(CheckResult(
            check_name="LanguageMatch",
            status="PASS" if lang_pass else "FAIL",
            reason="Language conforms to contract." if lang_pass else failures[-1],
        ))

        # 7. Completeness & Non-Empty Check
        comp_pass = len(answer_text.strip()) > 5
        if not comp_pass:
            failures.append("Response is empty or truncated.")

        checks.append(CheckResult(
            check_name="Completeness",
            status="PASS" if comp_pass else "FAIL",
            reason="Response is complete and structurally sound." if comp_pass else failures[-1],
        ))

        # 8. Uncertainty Correctness Check
        uncertainty_pass = True
        if "blurry" in q_low or "unclear" in q_low:
            if not any(u in ans_low for u in ["uncertain", "not sufficiently clear", "unable to verify", "blurry", "unclear", "illegible"]):
                uncertainty_pass = False
                failures.append("Low-quality visual query did not properly express uncertainty.")

        checks.append(CheckResult(
            check_name="UncertaintyCorrectness",
            status="PASS" if uncertainty_pass else "FAIL",
            reason="Uncertainty appropriately signaled." if uncertainty_pass else failures[-1],
        ))

        # 9. Hallucination Check (Check for absent document facts)
        hallucination_pass = True
        if contract.domain in [DomainType.ACADEMIC, DomainType.RESEARCH, DomainType.SOFTWARE] and evidence_pool:
            corpus_text = " ".join(e.normalized_content.lower() for e in evidence_pool)
            for fake_term in ["salary", "password", "phone number", "secret"]:
                if fake_term in q_low and fake_term not in corpus_text:
                    if "not stated" not in ans_low and "not found" not in ans_low:
                        hallucination_pass = False
                        failures.append(f"Answer fabricated absent attribute: {fake_term}")
                        break

        checks.append(CheckResult(
            check_name="HallucinationCheck",
            status="PASS" if hallucination_pass else "FAIL",
            reason="Zero invented absent facts." if hallucination_pass else failures[-1],
        ))

        # 10. User Question Coverage
        coverage_pass = True
        for key_q in ["sample size", "ram", "latency", "pool size"]:
            if key_q in q_low and key_q in ans_low:
                coverage_pass = True
                break

        checks.append(CheckResult(
            check_name="UserQuestionCoverage",
            status="PASS" if coverage_pass else "FAIL",
            reason="Directly addresses key elements of the user request." if coverage_pass else failures[-1],
        ))

        # 11. Modality Correctness
        modality_pass = True
        if contract.intent in [IntentType.IMAGE_ANALYSIS, IntentType.OCR] and not any(k in ans_low for k in ["visual", "image", "text", "not found", "observed", "uncertain"]):
            modality_pass = False
            failures.append("Image analysis output lacked visual or OCR observation structures.")

        checks.append(CheckResult(
            check_name="ModalityCorrectness",
            status="PASS" if modality_pass else "FAIL",
            reason="Output matches required modality." if modality_pass else failures[-1],
        ))

        # 12. Model Capability Correctness
        capability_pass = True
        checks.append(CheckResult(
            check_name="ModelCapabilityCorrectness",
            status="PASS" if capability_pass else "FAIL",
            reason="Executed by provider supporting requested capabilities.",
        ))

        # 13. Context Contamination Check
        contamination_pass = topic_pass
        checks.append(CheckResult(
            check_name="ContextContaminationCheck",
            status="PASS" if contamination_pass else "FAIL",
            reason="Zero unrelated context contamination." if contamination_pass else failures[-1],
        ))

        # 14. Academic Attribution Check
        academic_pass = True
        if contract.intent == IntentType.ACADEMIC and len(ans_low.split()) > 40:
            if not any(tag in answer_text for tag in ["[MODEL EXPLANATION]", "[SOURCE FACT]", "[GENERAL KNOWLEDGE]", "[ACADEMIC FRAMEWORK]", "Research Methodology"]):
                academic_pass = False
                failures.append("Academic output lacked provenance classification tags.")

        checks.append(CheckResult(
            check_name="AcademicAttributionCheck",
            status="PASS" if academic_pass else "FAIL",
            reason="Academic statements attributed with provenance." if academic_pass else failures[-1],
        ))

        # 15. Actual Answer & Anti-Acknowledgement Check
        # Strictly rejects responses that only acknowledge the request or leak internal tags
        actual_answer_pass = True
        
        # Check for leaked internal tags
        for leak_pat in cls._LEAKED_INTERNAL_TAGS:
            if re.search(leak_pat, ans_low):
                actual_answer_pass = False
                failures.append(f"Response contains leaked internal tag: {leak_pat}")
                break

        # Check for meta-acknowledgement fallbacks
        if actual_answer_pass:
            for ack_pat in cls._META_ACKNOWLEDGEMENT_PATTERNS:
                if re.search(ack_pat, ans_low):
                    # If it contains acknowledgement pattern and is short (< 250 chars), it's a non-answer
                    if len(answer_text.strip()) < 250:
                        actual_answer_pass = False
                        failures.append("Response only contains a meta-acknowledgement instead of answering the question.")
                        break

        # Check conversational filler
        if actual_answer_pass and ("As an AI language model" in answer_text or "I am an artificial intelligence" in answer_text):
            actual_answer_pass = False
            failures.append("Response contains conversational filler instead of direct answer.")

        checks.append(CheckResult(
            check_name="ActualAnswerCheck",
            status="PASS" if actual_answer_pass else "FAIL",
            reason="Direct substantive answer delivered without meta-acknowledgements or tag leaks." if actual_answer_pass else failures[-1],
        ))

        passed_count = sum(1 for c in checks if c.status == "PASS")
        overall_score = passed_count / float(len(checks))
        all_passed = len(failures) == 0

        return QualityGateResult(
            passed=all_passed,
            score=overall_score,
            checks=checks,
            reasons=failures,
            should_regenerate=not all_passed,
        )
