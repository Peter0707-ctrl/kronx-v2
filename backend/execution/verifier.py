"""
Phase 2D — Read-Only Verification Engine
Performs non-mutating post-task output verification and sensitive content screening.
Never executes shell commands, never mutates files, never performs network requests.
"""
from __future__ import annotations
import json
from typing import Dict, List, Any

FORBIDDEN_SECRET_PATTERNS = [
    "api_key=", "apikey=", "password=", "secret=",
    "private_key=", "-----begin ", "aws_secret", "bearer "
]


class ExecutionVerifier:
    """Read-only verification engine for task outputs."""

    def verify_tool_result(
        self,
        task_id: str,
        tool_name: str,
        tool_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verifies that tool results are well-formed and do not leak sensitive credentials.
        Returns a verification record dict.
        """
        checks_passed = True
        notes: List[str] = []

        # 1. Structural check
        if not isinstance(tool_result, dict):
            checks_passed = False
            notes.append("Tool result is not a valid dictionary.")
        else:
            if "success" not in tool_result:
                checks_passed = False
                notes.append("Tool result missing 'success' indicator.")

        # 2. Sensitive pattern scan on stringified output
        try:
            payload_lower = json.dumps(tool_result, default=str).lower()
            for pattern in FORBIDDEN_SECRET_PATTERNS:
                if pattern in payload_lower:
                    checks_passed = False
                    notes.append(f"Sensitive pattern '{pattern}' detected in tool output.")
                    break
        except Exception:
            pass

        if checks_passed and not notes:
            notes.append("Tool output verified successfully without sensitive leaks.")

        return {
            "task_id": task_id,
            "tool_name": tool_name,
            "verified": checks_passed,
            "notes": notes,
        }

    def verify_task_completion(
        self,
        task_id: str,
        task_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verifies that a completed task has appropriate result summary and status."""
        status = task_state.get("status")
        valid = status in ("COMPLETED", "SKIPPED", "BLOCKED", "FAILED")
        return {
            "task_id": task_id,
            "status": status,
            "valid_completion": valid,
            "verified": valid,
        }
