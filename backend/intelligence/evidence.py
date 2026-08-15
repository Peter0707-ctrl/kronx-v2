"""
Phase 4.0 — Multimodal Evidence Engine
Safe ingestion, normalization, section chunking, and provenance mapping for structured files and documents.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from intelligence.schemas import EvidenceItem, EvidenceProvenance
from llm.sanitizer import sanitize_secrets


class EvidenceEngine:
    """Extracts, normalizes, chunks, and indexes structured evidence from untrusted file data."""

    @staticmethod
    def calculate_sha256(content: str | bytes) -> str:
        if isinstance(content, str):
            content = content.encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def extract_from_text(
        cls,
        filename: str,
        content: str,
        source_type: str = "DOCUMENT_TEXT",
        chunk_size: int = 800,
    ) -> List[EvidenceItem]:
        """Extracts structured evidence chunks with paragraph/section provenance from text."""
        sanitized = sanitize_secrets(content)
        file_sha = cls.calculate_sha256(sanitized)
        file_id = f"src_{cls.calculate_sha256(filename)[:10]}"

        # Split into logical sections or paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n{2,}', sanitized) if p.strip()]
        if not paragraphs:
            paragraphs = [sanitized] if sanitized else []

        items: List[EvidenceItem] = []
        current_section = "Main Content"
        page_est = 1
        line_counter = 1

        for idx, para in enumerate(paragraphs, 1):
            # Check for header/section markers (e.g., "# Section", "Chapter 3:", "3.2 Methodology")
            header_match = re.match(r'^(?:#+\s*|Chapter\s+\d+:?|\d+\.\d+\s+)([A-Za-z0-9\s_-]+)', para, re.IGNORECASE)
            if header_match:
                current_section = header_match.group(1).strip()

            # Estimate page number (~300 words per page)
            words = len(para.split())
            if idx % 4 == 0:
                page_est += 1

            chunk_id = f"evi_{uuid.uuid4().hex[:10]}"
            items.append(
                EvidenceItem(
                    evidence_id=chunk_id,
                    source_file_id=file_id,
                    filename=filename,
                    source_type=source_type,
                    content=para,
                    normalized_content=para.lower().strip(),
                    sha256=cls.calculate_sha256(para),
                    extraction_method="structured_chunker",
                    confidence=1.0,
                    provenance=EvidenceProvenance(
                        source_file=filename,
                        source_type=source_type,
                        page=page_est,
                        section=current_section,
                        row_or_line=f"Paragraph {idx}",
                        confidence=1.0,
                    ),
                )
            )

        return items

    @classmethod
    def extract_from_tabular(cls, filename: str, content: str) -> List[EvidenceItem]:
        """Extracts structured evidence rows from CSV or TSV data."""
        sanitized = sanitize_secrets(content)
        file_id = f"src_{cls.calculate_sha256(filename)[:10]}"
        lines = [line.strip() for line in sanitized.splitlines() if line.strip()]
        if not lines:
            return []

        header = lines[0]
        items: List[EvidenceItem] = []

        # Store schema definition as first evidence item
        items.append(
            EvidenceItem(
                evidence_id=f"evi_{uuid.uuid4().hex[:10]}",
                source_file_id=file_id,
                filename=filename,
                source_type="CSV_SCHEMA",
                content=f"Columns: {header}",
                normalized_content=header.lower(),
                sha256=cls.calculate_sha256(header),
                provenance=EvidenceProvenance(
                    source_file=filename,
                    source_type="CSV_HEADER",
                    page=1,
                    section="Header",
                    row_or_line="Line 1",
                ),
            )
        )

        for row_idx, row in enumerate(lines[1:100], start=2):
            items.append(
                EvidenceItem(
                    evidence_id=f"evi_{uuid.uuid4().hex[:10]}",
                    source_file_id=file_id,
                    filename=filename,
                    source_type="CSV_ROW",
                    content=f"Row {row_idx}: {row}",
                    normalized_content=row.lower(),
                    sha256=cls.calculate_sha256(row),
                    provenance=EvidenceProvenance(
                        source_file=filename,
                        source_type="CSV_DATA",
                        page=1,
                        section="Table Data",
                        row_or_line=f"Row {row_idx}",
                    ),
                )
            )

        return items

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

            if score > 0.1:
                scored.append((item, min(1.0, score)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
