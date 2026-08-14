"""
Phase 2I.1 — Multimodal Document Analyzer
Analyzes PDFs, DOCX, and document structures with secret redaction and prompt-injection defense.
"""
import os
import base64
from typing import Dict, Any, List, Optional
from workspace.store import WorkspaceStore
from tools.path_verify import verify_safe_path


from multimodal.file_types import classify_file_type, FileCategory
from multimodal.limits import check_file_size, check_document_text_size
from multimodal.sanitizer import redact_secrets, detect_prompt_injection
from multimodal.schemas import (
    DocumentAnalysisResult,
    DocumentSection,
    DocumentTable,
    RiskLevel,
)
from multimodal.providers import ProviderRegistry
from multimodal.errors import (
    MultimodalError,
    FILE_NOT_FOUND,
    INVALID_REQUEST,
)


class DocumentAnalyzer:
    """Safely extracts structured intelligence, sections, and metadata from documents."""

    def __init__(self, workspace_store: Optional[WorkspaceStore] = None):
        self._workspace_store = workspace_store or WorkspaceStore()

    def analyze_document_file(
        self,
        workspace_id: str,
        relative_path: str,
        provider_name: Optional[str] = None,
    ) -> DocumentAnalysisResult:
        """Analyze a document file stored within the authorized workspace."""
        if not relative_path or not relative_path.strip():
            raise MultimodalError(INVALID_REQUEST, "Document path cannot be empty.")

        ws = self._workspace_store.get_workspace(workspace_id)
        if not ws:
            raise MultimodalError(INVALID_REQUEST, f"Workspace '{workspace_id}' not found.")

        ws_root = ws.get("root_path")
        if not ws_root or not os.path.exists(ws_root):
            raise MultimodalError(INVALID_REQUEST, f"Workspace root path does not exist on disk.")

        safe_path = verify_safe_path(ws_root, relative_path)
        if not os.path.exists(safe_path):
            raise MultimodalError(FILE_NOT_FOUND, f"Document '{relative_path}' not found.")

        size_bytes = os.path.getsize(safe_path)
        check_file_size(size_bytes)

        category, mime = classify_file_type(relative_path)
        with open(safe_path, "rb") as f:
            doc_bytes = f.read(size_bytes)

        return self.analyze_document_bytes(
            doc_bytes=doc_bytes,
            filename=os.path.basename(relative_path),
            mime_type=mime,
            provider_name=provider_name,
        )

    def analyze_document_bytes(
        self,
        doc_bytes: bytes,
        filename: str,
        mime_type: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> DocumentAnalysisResult:
        """Analyze raw document bytes with secret filtering and injection defense."""
        check_file_size(len(doc_bytes))
        category, norm_mime = classify_file_type(filename, mime_type)

        provider = ProviderRegistry.get_provider(provider_name)
        raw_res = provider.analyze_document(doc_bytes, norm_mime, filename)

        # Sanitize text
        text_preview = redact_secrets(raw_res.get("text_preview", ""))
        check_document_text_size(len(text_preview.encode("utf-8")))

        warnings = list(raw_res.get("warnings", []))
        warnings.extend(detect_prompt_injection(text_preview))
        # Deduplicate warnings
        warnings = list(dict.fromkeys(warnings))

        sections = [
            DocumentSection(
                title=s.get("title", "Section"),
                level=s.get("level", 1),
                content=redact_secrets(s.get("content", "")),
                page=s.get("page", 1),
            )
            for s in raw_res.get("sections", [])
        ]

        tables = [
            DocumentTable(
                headers=[redact_secrets(h) for h in t.get("headers", [])],
                rows=[[redact_secrets(c) for c in row] for row in t.get("rows", [])],
            )
            for t in raw_res.get("tables", [])
        ]

        facts = [redact_secrets(f) for f in raw_res.get("facts", [])]
        inferences = [redact_secrets(i) for i in raw_res.get("inferences", [])]
        assumptions = [redact_secrets(a) for a in raw_res.get("assumptions", [])]

        risk = RiskLevel.HIGH if warnings else RiskLevel.LOW

        return DocumentAnalysisResult(
            document_type=raw_res.get("document_type", "DOCUMENT"),
            page_count=raw_res.get("page_count", 1),
            sections=sections,
            tables=tables,
            metadata=raw_res.get("metadata", {}),
            text_preview=text_preview[:1000],
            word_count=raw_res.get("word_count", 0),
            facts=facts,
            inferences=inferences,
            assumptions=assumptions,
            warnings=warnings,
            risk_level=risk,
        )
