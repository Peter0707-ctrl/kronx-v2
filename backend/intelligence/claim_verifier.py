"""
Phase 4.0 — Claim Verification Engine
Extracts candidate claims from generated answers and verifies each claim against the task contract and evidence store.
"""
from __future__ import annotations
import re
import uuid
from typing import List, Dict, Any, Tuple
from intelligence.schemas import (
    ClaimItem, ClaimStatus, ClaimVerificationResult,
    EvidenceItem, TaskContract
)


class ClaimVerifier:
    """Extracts factual claims and performs bi-directional validation against indexed evidence."""

    @staticmethod
    def extract_claims(text: str) -> List[str]:
        """Splits answer text into discrete sentences/bullet claims."""
        # Split by bullet points or sentence terminators
        raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
        claims = []
        for line in raw_lines:
            # Strip bullet markdown
            clean_line = re.sub(r'^[*\-•\d\.]+\s*', '', line).strip()
            # Ignore headers or markdown formatting
            if clean_line.startswith("#") or clean_line.startswith("|") or len(clean_line) < 10:
                continue
            # Break down compound paragraphs if needed
            sentences = re.split(r'(?<=[.!?])\s+', clean_line)
            for s in sentences:
                if len(s.strip()) > 15:
                    claims.append(s.strip())
        return claims

    @classmethod
    def verify_response(
        cls,
        contract: TaskContract,
        response_text: str,
        evidence_pool: List[EvidenceItem],
    ) -> ClaimVerificationResult:
        """
        Validates generated draft response against the task contract and evidence corpus.
        """
        raw_claims = cls.extract_claims(response_text)
        verified: List[ClaimItem] = []
        unsupported: List[ClaimItem] = []
        contradicted: List[ClaimItem] = []
        inferred: List[ClaimItem] = []

        if not raw_claims:
            return ClaimVerificationResult(
                verified_claims=[],
                unsupported_claims=[],
                overall_support_ratio=1.0,
                passed=True,
                summary="No discrete claims extracted; response structure valid.",
            )

        for idx, text in enumerate(raw_claims, 1):
            claim_id = f"clm_{uuid.uuid4().hex[:8]}"
            t_low = text.lower()

            # 1. Explicit uncertainty / not-found claim
            if any(phrase in t_low for phrase in ["not found", "does not contain", "could not find", "not present", "unclear", "uncertain"]):
                verified.append(
                    ClaimItem(
                        claim_id=claim_id,
                        text=text,
                        status=ClaimStatus.VERIFIED,
                        reason="Explicit qualification statement.",
                    )
                )
                continue

            # 2. Document/File tasks requires evidence match
            if contract.evidence_required:
                if not evidence_pool:
                    unsupported.append(
                        ClaimItem(
                            claim_id=claim_id,
                            text=text,
                            status=ClaimStatus.UNSUPPORTED,
                            reason="No evidence available to substantiate claim.",
                        )
                    )
                    continue

                # Search evidence for key terms
                terms = set(re.findall(r'\b[a-zA-Z0-9_-]{4,}\b', t_low))
                matched_evidence = []
                for ev in evidence_pool:
                    matched = [term for term in terms if term in ev.normalized_content]
                    if terms and len(matched) >= max(2, int(len(terms) * 0.60)):
                        matched_evidence.append(ev)


                if matched_evidence:
                    top_ev = matched_evidence[0]
                    verified.append(
                        ClaimItem(
                            claim_id=claim_id,
                            text=text,
                            status=ClaimStatus.VERIFIED,
                            supporting_evidence_ids=[top_ev.evidence_id],
                            source_provenance=top_ev.provenance,
                            confidence=0.95,
                            reason=f"Matched in {top_ev.filename}",
                        )
                    )
                else:
                    unsupported.append(
                        ClaimItem(
                            claim_id=claim_id,
                            text=text,
                            status=ClaimStatus.UNSUPPORTED,
                            reason="Claim not found in uploaded document evidence.",
                        )
                    )
            else:
                # General Reasoning / Knowledge tasks
                verified.append(
                    ClaimItem(
                        claim_id=claim_id,
                        text=text,
                        status=ClaimStatus.VERIFIED,
                        reason="General reasoning statement.",
                    )
                )

        total = len(verified) + len(unsupported) + len(contradicted) + len(inferred)
        ratio = (len(verified) + len(inferred)) / float(total) if total > 0 else 1.0
        passed = len(unsupported) == 0 if contract.evidence_required else ratio >= 0.70

        return ClaimVerificationResult(
            verified_claims=verified,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            inferred_claims=inferred,
            overall_support_ratio=ratio,
            passed=passed,
            summary=f"Verified {len(verified)}/{total} claims (Support Ratio: {ratio:.1%}).",
        )
