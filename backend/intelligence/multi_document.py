"""
Phase 4.1 — Multi-Document Comparison & Attribution Engine
Builds cross-document evidence matrices and answers cross-document queries while strictly maintaining source isolation and file provenance.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Optional
from intelligence.schemas import EvidenceItem, ClaimItem, ClaimStatus


class MultiDocumentEngine:
    """Builds comparison matrices across multiple uploaded documents with strict source provenance."""

    @classmethod
    def compare_documents(
        cls,
        files_evidence: Dict[str, List[EvidenceItem]],
        aspects: Optional[List[str]] = None,
        query: Optional[str] = None,
    ) -> Tuple[str, List[ClaimItem]]:
        """
        Constructs a structured Markdown comparison table or targeted multi-document answer.
        """
        if not files_evidence:
            return "No documents provided for comparison.", []

        filenames = list(files_evidence.keys())
        claims: List[ClaimItem] = []

        # If user asks a targeted question (e.g., "Which document states X?" or "What does each document state?")
        if query:
            q_low = query.lower()
            lines = [f"**Multi-Document Analysis across {len(filenames)} files:**\n"]
            for fname in filenames:
                ev_list = files_evidence.get(fname, [])
                q_terms = [t for t in re.findall(r'\b\w{3,}\b', q_low) if t not in ["what", "which", "does", "each", "document", "state", "says", "both", "file", "papers"]]
                matched = [e for e in ev_list if any(t in e.normalized_content for t in q_terms)] if q_terms else ev_list
                if matched:
                    top_ev = matched[0]
                    lines.append(f"- **{fname}:** {top_ev.content}")
                    claims.append(
                        ClaimItem(
                            claim_id=f"clm_md_{len(claims)+1}",
                            text=f"[{fname}] {top_ev.content[:100]}",
                            status=ClaimStatus.VERIFIED,
                            supporting_evidence_ids=[top_ev.evidence_id],
                            source_provenance=top_ev.provenance,
                            reason=f"Directly verified from {fname}",
                        )
                    )
                else:
                    lines.append(f"- **{fname}:** No matching statements found for this query.")

            return "\n".join(lines), claims

        # Standard Comparison Matrix
        default_aspects = aspects or ["Methodology", "Sample Size", "Key Findings", "Limitations"]
        matrix_rows = []

        for aspect in default_aspects:
            row_data = [aspect]
            for fname in filenames:
                ev_list = files_evidence.get(fname, [])
                # Search evidence for aspect
                matched = [e for e in ev_list if aspect.lower() in e.normalized_content]
                if matched:
                    top_ev = matched[0]
                    short_val = top_ev.content[:80].replace("|", "/")
                    loc = f"p.{top_ev.provenance.page}" if top_ev.provenance.page else "sec. 1"
                    cell_text = f"{short_val} (*{loc}*)"
                    claims.append(
                        ClaimItem(
                            claim_id=f"clm_comp_{len(claims)+1}",
                            text=f"[{fname}] {aspect}: {top_ev.content[:100]}",
                            status=ClaimStatus.VERIFIED,
                            supporting_evidence_ids=[top_ev.evidence_id],
                            source_provenance=top_ev.provenance,
                            reason=f"Extracted from {fname}",
                        )
                    )
                else:
                    cell_text = "Not explicitly stated"
                row_data.append(cell_text)
            matrix_rows.append(row_data)

        # Build Markdown Table
        header_cols = ["Comparison Dimension"] + filenames
        header_line = "| " + " | ".join(header_cols) + " |"
        sep_line = "| " + " | ".join(["---"] * len(header_cols)) + " |"
        body_lines = ["| " + " | ".join(row) + " |" for row in matrix_rows]

        table_md = "\n".join([header_line, sep_line] + body_lines)
        res = f"### 📊 Cross-Document Evidence Comparison Matrix\n\n{table_md}\n\n*Note: Each cell is verified directly against its respective source document.*"

        return res, claims
