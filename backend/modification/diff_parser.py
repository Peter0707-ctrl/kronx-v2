"""
Phase 2E — Deterministic Diff & Patch Parser
Interprets structured file patches and unified diffs.
Calculates additions, deletions, modifications, and target file state deterministically.
"""
from __future__ import annotations
import difflib
from typing import Dict, List, Optional, Tuple, Any

from modification.schemas import FilePatch, FileOperationType
from modification.errors import ModificationError, INVALID_PATCH_SYNTAX


class DiffParser:
    """Parser and evaluator for file patches."""

    @staticmethod
    def parse_patch_metrics(patch: FilePatch) -> Tuple[int, int, int]:
        """
        Calculates (additions, deletions, modifications) for a given FilePatch.
        """
        additions = 0
        deletions = 0
        modifications = 0

        if patch.operation == FileOperationType.CREATE:
            content = patch.new_content or ""
            additions = len(content.splitlines())
            modifications = 1
        elif patch.operation == FileOperationType.DELETE:
            deletions = 1
            modifications = 1
        elif patch.operation == FileOperationType.RENAME:
            modifications = 1
        elif patch.operation == FileOperationType.MODIFY:
            modifications = 1
            if patch.diff_content:
                for line in patch.diff_content.splitlines():
                    if line.startswith("+") and not line.startswith("+++"):
                        additions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1
            elif patch.new_content is not None:
                additions = len(patch.new_content.splitlines())

        return additions, deletions, modifications

    @staticmethod
    def apply_patch_to_text(original_text: str, patch: FilePatch) -> str:
        """
        Applies patch to original_text to compute expected new text.
        Supports direct new_content replacement or unified diff chunk application.
        """
        if patch.operation == FileOperationType.CREATE:
            return patch.new_content or ""

        if patch.operation == FileOperationType.DELETE:
            return ""

        if patch.operation == FileOperationType.RENAME:
            return patch.new_content if patch.new_content is not None else original_text

        # MODIFY
        if patch.new_content is not None:
            return patch.new_content

        if patch.diff_content:
            return DiffParser._apply_unified_diff(original_text, patch.diff_content)

        raise ModificationError(INVALID_PATCH_SYNTAX, f"Patch for '{patch.path}' has neither 'new_content' nor 'diff_content'.")

    @staticmethod
    def _apply_unified_diff(original_text: str, diff_text: str) -> str:
        """
        Apply a standard unified diff string to original_text.
        """
        orig_lines = original_text.splitlines(keepends=True)
        # Standardize line endings
        diff_lines = diff_text.splitlines(keepends=True)

        # Parse hunks
        new_lines: List[str] = []
        orig_idx = 0
        in_hunk = False

        for line in diff_lines:
            if line.startswith("@@"):
                in_hunk = True
                continue
            if not in_hunk:
                continue

            if line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith("-"):
                orig_idx += 1
            elif line.startswith(" ") or line.startswith("\t"):
                if orig_idx < len(orig_lines):
                    new_lines.append(orig_lines[orig_idx])
                    orig_idx += 1
                else:
                    new_lines.append(line[1:])
            else:
                # Line without prefix in hunk, treat as context
                if orig_idx < len(orig_lines):
                    new_lines.append(orig_lines[orig_idx])
                    orig_idx += 1

        # Append remaining original lines
        while orig_idx < len(orig_lines):
            new_lines.append(orig_lines[orig_idx])
            orig_idx += 1

        return "".join(new_lines)

    @staticmethod
    def generate_unified_diff(original_text: str, new_text: str, filename: str) -> str:
        """Helper to generate standard unified diff for preview."""
        orig_lines = original_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        )
        return "\n".join(diff)
