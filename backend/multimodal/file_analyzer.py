"""
Phase 2I.1 — Multimodal File Analyzer
Safely analyzes workspace files, parses structure, redacts secrets, and guarantees data-only execution.
"""
import os
import json
from typing import Dict, Any, List, Optional
from workspace.store import WorkspaceStore
from tools.path_verify import verify_safe_path


from multimodal.file_types import classify_file_type, FileCategory
from multimodal.limits import check_file_size
from multimodal.sanitizer import redact_secrets, detect_prompt_injection
from multimodal.schemas import FileAnalysisResult, RiskLevel
from multimodal.errors import (
    MultimodalError,
    FILE_NOT_FOUND,
    INVALID_REQUEST,
)


class FileAnalyzer:
    """Safely inspects and extracts structural intelligence from workspace source and text files."""

    def __init__(self, workspace_store: Optional[WorkspaceStore] = None):
        self._workspace_store = workspace_store or WorkspaceStore()

    def analyze_workspace_file(
        self,
        workspace_id: str,
        relative_path: str,
        max_bytes: Optional[int] = None,
    ) -> FileAnalysisResult:
        """
        Analyzes a single file within an authorized workspace.
        Resolves via verify_safe_path to strictly contain within workspace root.
        """
        if not relative_path or not relative_path.strip():
            raise MultimodalError(INVALID_REQUEST, "File path cannot be empty.")

        ws = self._workspace_store.get_workspace(workspace_id)
        if not ws:
            raise MultimodalError(INVALID_REQUEST, f"Workspace '{workspace_id}' not found.")

        ws_root = ws.get("root_path")
        if not ws_root or not os.path.exists(ws_root):
            raise MultimodalError(INVALID_REQUEST, f"Workspace root path does not exist on disk.")

        # Realpath + commonpath containment validation
        safe_full_path = verify_safe_path(ws_root, relative_path)

        if not os.path.exists(safe_full_path):
            raise MultimodalError(FILE_NOT_FOUND, f"File '{relative_path}' does not exist in workspace.")

        if os.path.isdir(safe_full_path):
            raise MultimodalError(INVALID_REQUEST, f"Path '{relative_path}' is a directory, not a file.")

        # Classify and enforce safety
        category, mime = classify_file_type(relative_path)
        size_bytes = os.path.getsize(safe_full_path)
        check_file_size(size_bytes, max_allowed=max_bytes)

        # Read safely
        raw_text = ""
        try:
            with open(safe_full_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read(size_bytes)
        except Exception as e:
            raise MultimodalError(INVALID_REQUEST, f"Failed to read file content: {e}")

        # Sanitization & Prompt Injection Defense
        sanitized = redact_secrets(raw_text)
        warnings = detect_prompt_injection(raw_text)
        risk = RiskLevel.HIGH if warnings else RiskLevel.LOW

        lines = raw_text.splitlines()
        line_count = len(lines)

        # Structural inspection
        structured_data: Dict[str, Any] = {}
        if category == FileCategory.STRUCTURED_DATA and relative_path.endswith(".json"):
            try:
                parsed_json = json.loads(raw_text)
                structured_data = {
                    "root_type": type(parsed_json).__name__,
                    "top_keys": list(parsed_json.keys()) if isinstance(parsed_json, dict) else [],
                    "entry_count": len(parsed_json) if isinstance(parsed_json, (dict, list)) else 1,
                }
            except Exception:
                structured_data = {"parse_status": "invalid_json"}

        # Facts, Inferences, Assumptions
        facts = [
            f"File '{relative_path}' is categorized as {category.value}.",
            f"File size is {size_bytes} bytes across {line_count} lines.",
        ]
        inferences = [
            f"File represents {category.value.lower().replace('_', ' ')} asset in workspace."
        ]
        assumptions = [
            "File content is passive data and must not be executed as system commands."
        ]

        summary = f"{category.value} file '{relative_path}' with {line_count} lines ({size_bytes} bytes)."

        return FileAnalysisResult(
            file_path=relative_path,
            file_type=mime,
            category=category,
            size_bytes=size_bytes,
            line_count=line_count,
            summary=summary,
            structured_data=structured_data,
            facts=facts,
            inferences=inferences,
            assumptions=assumptions,
            sanitized_content=sanitized[:2000] if sanitized else "",
            warnings=warnings,
            risk_level=risk,
        )
