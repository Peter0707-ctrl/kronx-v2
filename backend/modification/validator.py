"""
Phase 2E — Comprehensive Patch Validator
Enforces all 18 validation steps before any modification proposal or apply operation.
"""
from __future__ import annotations
import os
from typing import Dict, List, Optional, Tuple, Any

from tools.path_verify import verify_safe_path
from workspace.store import WorkspaceStore
from planner.store import PlannerStore
from execution.checkpoint import ExecutionStore
from modification.schemas import (
    PatchPayload, FilePatch, FileOperationType, ModificationMode,
    MAX_PATCH_SIZE_BYTES, MAX_FILES_PER_PATCH, MAX_FILE_WRITE_BYTES,
    MAX_TOTAL_WRITE_BYTES, MAX_ADDITIONS, MAX_DELETIONS,
)
from modification.sensitive import SensitiveFileDetector
from modification.diff_parser import DiffParser
from modification.stores import AuthorizationStore
from modification.errors import (
    ModificationError,
    EMPTY_PATCH,
    INVALID_PATCH_SYNTAX,
    WORKSPACE_NOT_AUTHORIZED,
    PLAN_NOT_FOUND,
    EXECUTION_NOT_FOUND,
    TASK_NOT_FOUND,
    AUTHORIZATION_NOT_FOUND,
    AUTHORIZATION_EXPIRED,
    AUTHORIZATION_CONSUMED,
    AUTHORIZATION_REVOKED,
    PATH_OUTSIDE_WORKSPACE,
    ABSOLUTE_PATH_REJECTED,
    SENSITIVE_FILE,
    BLOCKED_SENSITIVE_CONTENT,
    BINARY_FILE_BLOCKED,
    GENERATED_PATH_BLOCKED,
    RESOURCE_LIMIT,
    BLOCKED_REQUIRES_PERMISSION,
    PERMISSION_DENIED,
    FORBIDDEN_PERMISSION_LEVEL,
)


class PatchValidator:
    """Validator implementing full multi-layer security validation for file modifications."""

    def __init__(
        self,
        ws_store: Optional[WorkspaceStore] = None,
        plan_store: Optional[PlannerStore] = None,
        exec_store: Optional[ExecutionStore] = None,
        auth_store: Optional[AuthorizationStore] = None,
    ):
        self._ws_store   = ws_store or WorkspaceStore()
        self._plan_store = plan_store or PlannerStore()
        self._exec_store = exec_store or ExecutionStore()
        self._auth_store = auth_store or AuthorizationStore()

    def validate_proposal(
        self,
        workspace_id: str,
        patch_payload: PatchPayload,
        plan_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Tuple[str, List[str], List[str], int, int, int]:
        """
        Validates a modification proposal.
        Returns (workspace_root, affected_files, warnings, total_additions, total_deletions, total_mods).
        """
        # 1. Non-empty patch validation
        if not patch_payload.patches:
            raise ModificationError(EMPTY_PATCH, "Patch payload contains no file patches.")

        # 2. Workspace Authorization Check
        ws_data = self._ws_store.get_workspace(workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise ModificationError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{workspace_id}' is not authorized.")
        workspace_root = ws_data["root_path"]

        # 3. Plan Validation (if provided)
        if plan_id:
            plan_data = self._plan_store.get_plan(plan_id)
            if not plan_data:
                raise ModificationError(PLAN_NOT_FOUND, f"Plan '{plan_id}' not found.")
            if plan_data.get("workspace_id") != workspace_id:
                raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Plan does not belong to the specified workspace.")

        # 4. Execution Validation (if provided)
        if execution_id:
            exec_data = self._exec_store.get_execution(execution_id)
            if not exec_data:
                raise ModificationError(EXECUTION_NOT_FOUND, f"Execution '{execution_id}' not found.")
            if exec_data.get("workspace_id") != workspace_id:
                raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Execution does not belong to the specified workspace.")

        # 5. Resource Limits
        if len(patch_payload.patches) > MAX_FILES_PER_PATCH:
            raise ModificationError(RESOURCE_LIMIT, f"Too many files in patch ({len(patch_payload.patches)} > {MAX_FILES_PER_PATCH}).")

        affected_files: List[str] = []
        warnings: List[str] = []
        total_adds = 0
        total_dels = 0
        total_mods = 0
        total_bytes = 0

        # 6. Per-patch validations
        for p in patch_payload.patches:
            # A. Relative path check
            if p.path.startswith("/") or p.path.startswith("\\") or (len(p.path) > 1 and p.path[1] == ":"):
                raise ModificationError(ABSOLUTE_PATH_REJECTED, f"Absolute path '{p.path}' is rejected.")

            # B. Containment validation
            try:
                canonical_path = verify_safe_path(workspace_root, p.path)
            except ValueError:
                raise ModificationError(PATH_OUTSIDE_WORKSPACE, f"Path '{p.path}' escapes workspace boundary.")

            # C. Sensitive file checks
            is_sens, sens_reason = SensitiveFileDetector.is_sensitive_path(p.path)
            if is_sens:
                raise ModificationError(SENSITIVE_FILE, f"Modification of sensitive file '{p.path}' is forbidden: {sens_reason}")

            # D. Generated directory checks
            is_gen, gen_reason = SensitiveFileDetector.is_generated_path(p.path)
            if is_gen:
                raise ModificationError(GENERATED_PATH_BLOCKED, f"Modification of generated path '{p.path}' is blocked: {gen_reason}")

            # E. Binary file checks
            is_bin, bin_reason = SensitiveFileDetector.is_binary_path(p.path)
            if is_bin:
                raise ModificationError(BINARY_FILE_BLOCKED, f"Binary modification for '{p.path}' is blocked: {bin_reason}")

            # F. Rename checks
            if p.operation == FileOperationType.RENAME:
                if not p.new_path:
                    raise ModificationError(INVALID_PATCH_SYNTAX, "RENAME operation requires 'new_path'.")
                try:
                    verify_safe_path(workspace_root, p.new_path)
                except ValueError:
                    raise ModificationError(PATH_OUTSIDE_WORKSPACE, f"Destination path '{p.new_path}' escapes workspace boundary.")
                r_sens, r_reason = SensitiveFileDetector.is_sensitive_path(p.new_path)
                if r_sens:
                    raise ModificationError(SENSITIVE_FILE, f"Rename destination '{p.new_path}' is sensitive.")

            # G. Defensive secret detection
            content_to_scan = p.new_content or p.diff_content or ""
            is_sec, sec_reason = SensitiveFileDetector.scan_for_secrets(content_to_scan)
            if is_sec:
                raise ModificationError(BLOCKED_SENSITIVE_CONTENT, f"Defensive secret check failed on '{p.path}': {sec_reason}")

            # H. Metrics & byte limits
            content_len = len(content_to_scan.encode("utf-8"))
            if content_len > MAX_FILE_WRITE_BYTES:
                raise ModificationError(RESOURCE_LIMIT, f"File write payload for '{p.path}' exceeds limit of {MAX_FILE_WRITE_BYTES} bytes.")
            total_bytes += content_len

            adds, dels, mods = DiffParser.parse_patch_metrics(p)
            total_adds += adds
            total_dels += dels
            total_mods += mods
            affected_files.append(p.path)

        if total_bytes > MAX_TOTAL_WRITE_BYTES:
            raise ModificationError(RESOURCE_LIMIT, f"Total write payload exceeds limit of {MAX_TOTAL_WRITE_BYTES} bytes.")

        if total_adds > MAX_ADDITIONS or total_dels > MAX_DELETIONS:
            raise ModificationError(RESOURCE_LIMIT, "Patch exceeds maximum allowed line additions or deletions.")

        return workspace_root, affected_files, warnings, total_adds, total_dels, total_mods

    def validate_apply_authorization(
        self,
        workspace_id: str,
        proposal_id: str,
        authorization_id: str,
    ) -> None:
        """
        Validates authorization record before applying changes.
        """
        if not authorization_id:
            raise ModificationError(BLOCKED_REQUIRES_PERMISSION, "Applying a modification requires an explicit authorization_id.")

        auth_data = self._auth_store.get_item(authorization_id)
        if not auth_data:
            raise ModificationError(AUTHORIZATION_NOT_FOUND, f"Authorization '{authorization_id}' not found.")

        # Cross-workspace validation
        if auth_data.get("workspace_id") != workspace_id:
            raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Authorization does not match the target workspace.")

        # Proposal binding validation
        if auth_data.get("proposal_id") != proposal_id:
            raise ModificationError(BLOCKED_REQUIRES_PERMISSION, "Authorization record does not match the proposal_id.")

        # Status check
        status = auth_data.get("status")
        if status == "CONSUMED":
            raise ModificationError(AUTHORIZATION_CONSUMED, "This authorization token has already been consumed.")
        if status == "EXPIRED":
            raise ModificationError(AUTHORIZATION_EXPIRED, "This authorization has expired.")
        if status == "REVOKED":
            raise ModificationError(AUTHORIZATION_REVOKED, "This authorization has been revoked.")
        if status != "APPROVED":
            raise ModificationError(BLOCKED_REQUIRES_PERMISSION, f"Authorization status is '{status}', expected 'APPROVED'.")

        # Expiration timestamp check
        expires_at_str = auth_data.get("expires_at")
        if expires_at_str:
            try:
                from datetime import datetime, timezone
                now_utc = datetime.now(timezone.utc)
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                is_expired = now_utc > expires_at
            except Exception:
                is_expired = False

            if is_expired:
                auth_data["status"] = "EXPIRED"
                self._auth_store.save_item(authorization_id, auth_data)
                raise ModificationError(AUTHORIZATION_EXPIRED, "Authorization token has expired.")

