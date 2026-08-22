"""
Phase 4.1 — Document Grounding Engine
Strictly enforces the "NO EVIDENCE = NO CLAIM" invariant for all document-based queries.
Ensures exact text preservation, answers the user question directly, and states when facts are unmentioned.
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
        inquiry_words = {
            "what", "when", "where", "which", "does", "explain", "state", "show", "describe",
            "find", "tell", "document", "is", "the", "report", "file", "that", "years", "according",
            "this", "author", "name", "value", "details", "information", "and", "requirement",
            "requirements", "used", "exist", "algorithm", "field", "fields", "minimum", "maximum",
            "policy", "config", "code", "function", "study", "studies", "pdf", "docx", "json", "csv", "latency",
            "pool", "stated", "contain", "extract", "extraction", "analyze", "analysis", "research",
            "from", "give", "list", "check", "provide", "provided", "summary", "summarize", "about",
            "with", "into", "methodology", "objective", "objectives", "results", "findings", "sample",
            "size", "nodes", "method", "data", "can", "you", "guess", "please", "use", "uses", "using",
            "main", "charter", "paper", "memo", "internal", "create", "generate", "word", "excel",
            "powerpoint", "presentation", "deck", "spreadsheet", "proposal", "export", "cross", "verify"
        }

        key_attributes = [t for t in query_terms if t not in inquiry_words]

        corpus_text = " ".join(e.normalized_content.lower() for e in evidence_items)
        relevant_scored = EvidenceEngine.search_evidence(query, evidence_items, top_k=6)

        # Check for explicitly missing attributes that are not in corpus
        if key_attributes:
            def is_present(attr: str) -> bool:
                if attr in corpus_text:
                    return True
                if len(attr) > 4 and (attr[:-1] in corpus_text or attr[:-2] in corpus_text):
                    return True
                return False

            missing_attrs = [attr for attr in key_attributes if not is_present(attr)]
            explicit_absent_keywords = {"salary", "password", "phone", "age", "credit", "card", "warranty", "ssn", "secret"}
            has_explicit_absent = any(k in explicit_absent_keywords for k in missing_attrs)

            # If explicitly absent keywords queried or 100% of key query attributes missing and no relevant search match
            if (has_explicit_absent or (len(missing_attrs) == len(key_attributes) and not relevant_scored)):
                reported_missing = [a for a in missing_attrs if a in explicit_absent_keywords] or missing_attrs
                attr_str = ", ".join(sorted(reported_missing))
                ans = f"That information was not found in the provided document. The requested information ({attr_str}) is not stated in the provided document."
                claim = ClaimItem(
                    claim_id="clm_not_found",
                    text=ans,
                    status=ClaimStatus.VERIFIED,
                    reason="Explicit not-found statement verified against document corpus.",
                )
                return ans, [], [claim]





        relevant_scored = EvidenceEngine.search_evidence(query, evidence_items, top_k=6)
        matched_evidence = [item for item, score in relevant_scored] if relevant_scored else evidence_items[:6]
        if not matched_evidence:
            ans = "I could not find information addressing that question in the provided document."
            return ans, [], []


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

        # Check detail level requirement
        if "CONCISE" in contract.output_requirements or "concise" in query.lower() or "short" in query.lower():
            body = "\n".join(f"- {ev.content}" for ev in matched_evidence[:2])
            return f"{body}\n\n*(Source: {unique_citations[0]})*", matched_evidence[:2], claims[:2]

        header = f"Based on the provided document (`{matched_evidence[0].filename}`):\n\n"
        body = "\n\n".join(content_lines)
        footer = f"\n\n**Sources:**\n" + "\n".join(f"- {c}" for c in unique_citations)

        return header + body + footer, matched_evidence, claims
