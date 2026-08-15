"""
Phase 4.1 — Multimodal Evidence Engine
Safe ingestion, normalization, section chunking, and provenance mapping for structured files and documents.
Delegates to SpecializedParsers to guarantee exact text preservation and zero hallucination.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple

from intelligence.schemas import EvidenceItem, EvidenceProvenance
from intelligence.parsers import SpecializedParsers
from llm.sanitizer import sanitize_secrets


class EvidenceEngine:
    """Extracts, normalizes, chunks, and indexes structured evidence from untrusted file data."""

    @staticmethod
    def calculate_sha256(content: str | bytes) -> str:
        return SpecializedParsers.calculate_sha256(content)

    @classmethod
    def extract_by_file_type(cls, filename: str, content: str, file_type: Optional[str] = None) -> List[EvidenceItem]:
        """
        Dispatches to the appropriate specialized parser based on extension and content structure.
        """
        f_lower = filename.lower()
        t_lower = (file_type or "").lower()

        if f_lower.endswith(".pdf") or t_lower == "pdf":
            return SpecializedParsers.parse_pdf(filename, content)
        elif f_lower.endswith(".docx") or f_lower.endswith(".doc") or t_lower in ["docx", "doc"]:
            return SpecializedParsers.parse_docx(filename, content)
        elif f_lower.endswith(".csv") or t_lower == "csv":
            return SpecializedParsers.parse_csv_or_tsv(filename, content, delimiter=",")
        elif f_lower.endswith(".tsv") or t_lower == "tsv":
            return SpecializedParsers.parse_csv_or_tsv(filename, content, delimiter="\t")
        elif f_lower.endswith(".json") or t_lower == "json":
            return SpecializedParsers.parse_json(filename, content)
        elif any(f_lower.endswith(ext) for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".rs", ".sql", ".html", ".css"]) or t_lower in ["code", "source_code"]:
            return SpecializedParsers.parse_source_code(filename, content)
        else:
            return SpecializedParsers.parse_txt_or_md(filename, content)

    @classmethod
    def extract_from_text(
        cls,
        filename: str,
        content: str,
        source_type: str = "DOCUMENT_TEXT",
        chunk_size: int = 800,
    ) -> List[EvidenceItem]:
        """Extracts structured evidence chunks with paragraph/section provenance from text."""
        return cls.extract_by_file_type(filename, content, file_type="text")

    @classmethod
    def extract_from_tabular(cls, filename: str, content: str) -> List[EvidenceItem]:
        """Extracts structured evidence rows from CSV or TSV data."""
        return SpecializedParsers.parse_csv_or_tsv(filename, content, delimiter=",")

    @classmethod
    def search_evidence(
        cls,
        query: str,
        evidence_pool: List[EvidenceItem],
        top_k: int = 5,
    ) -> List[Tuple[EvidenceItem, float]]:
        """Searches evidence items for query relevance using exact phrase and keyword overlap."""
        if not evidence_pool or not query:
            return []

        q_terms = set(re.findall(r'\b[a-zA-Z0-9_-]{3,}\b', query.lower()))
        scored: List[Tuple[EvidenceItem, float]] = []

        for item in evidence_pool:
            score = 0.0
            norm = item.normalized_content

            # Exact substring match gives high confidence
            if query.lower() in norm:
                score += 0.8

            # Keyword matches
            matched_terms = [t for t in q_terms if t in norm]
            if q_terms:
                term_ratio = len(matched_terms) / len(q_terms)
                score += term_ratio * 0.5

            if score >= 0.05:
                scored.append((item, min(1.0, score)))


        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

