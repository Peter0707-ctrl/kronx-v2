"""
Phase 4.0 — Document Grounding Engine
Strictly enforces the "NO EVIDENCE = NO CLAIM" invariant for all document-based queries.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional, Tuple
from intelligence.schemas import EvidenceItem, TaskContract, ClaimItem, ClaimStatus
from intelligence.evidence import EvidenceEngine


class DocumentGroundingEngine:
    """Answers queries strictly based on extracted document evidence, rejecting ungrounded assumptions."""

    @classmethod
    def answer_from_evidence(
        cls,
        contract: TaskContract,
        evidence_items: List[EvidenceItem],
        query: str,
    ) -> Tuple[str, List[EvidenceItem], List[ClaimItem]]:
        """
        Synthesizes an evidence-grounded answer or states that information is not present in the document.
        """
        if not evidence_items:
            ans = "The provided document does not contain any readable content to answer this question."
            return ans, [], []

        # Check if the query asks about specific attributes that do NOT exist anywhere in the corpus
        query_terms = set(re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', query.lower()))
        inquiry_words = {"what", "when", "where", "which", "does", "explain", "state", "show", "describe", "find", "tell", "document", "is", "the", "report", "file", "that", "years"}
        key_attributes = [t for t in query_terms if t not in inquiry_words]

        if key_attributes:
            corpus_text = " ".join(e.normalized_content for e in evidence_items)
            missing_attrs = [attr for attr in key_attributes if attr not in corpus_text]
            if missing_attrs:
                ans = f"That information was not found in the provided document. The document does not contain details regarding {', '.join(sorted(missing_attrs))}."
                claim = ClaimItem(
                    claim_id="clm_not_found",
                    text=ans,
                    status=ClaimStatus.VERIFIED,
                    reason="Explicit not-found statement verified against document corpus.",
                )
                return ans, [], [claim]


        relevant_scored = EvidenceEngine.search_evidence(query, evidence_items, top_k=6)
        if not relevant_scored:
            ans = "I could not find information addressing that question in the provided document."
            return ans, [], []


        matched_evidence = [item for item, score in relevant_scored]
        
        # Formulate grounded answer with explicit citations
        citations = []
        claims: List[ClaimItem] = []
        content_lines = []

        for idx, ev in enumerate(matched_evidence, 1):
            prov = ev.provenance
            loc_str = f"{prov.source_file}"
            if prov.page:
                loc_str += f", Page {prov.page}"
            if prov.section:
                loc_str += f" ({prov.section})"

            content_lines.append(f"- **{loc_str}:** {ev.content}")
            citations.append(loc_str)
            claims.append(
                ClaimItem(
                    claim_id=f"clm_{idx}",
                    text=ev.content[:150],
                    status=ClaimStatus.VERIFIED,
                    supporting_evidence_ids=[ev.evidence_id],
                    confidence=ev.confidence,
                    source_provenance=prov,
                    reason=f"Directly verified from {loc_str}",
                )
            )

        unique_citations = list(dict.fromkeys(citations))
        header = f"Based on the provided document (`{matched_evidence[0].filename}`):\n\n"
        body = "\n\n".join(content_lines)
        footer = f"\n\n**Sources:**\n" + "\n".join(f"- {c}" for c in unique_citations)

        return header + body + footer, matched_evidence, claims
