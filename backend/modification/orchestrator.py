"""
Phase 2E — Modification Orchestrator
Coordinates the 3-stage modification pipeline: PROPOSE → PREVIEW → APPROVE → APPLY / ROLLBACK.
Strictly requires server-side authorization before write; enforces atomic replacement,
optimistic hash checks, post-write verification, and rollback capabilities.
"""
from __future__ import annotations
import os
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

from tools.path_verify import verify_safe_path
from workspace.store import WorkspaceStore
from planner.store import PlannerStore
from execution.checkpoint import ExecutionStore
from modification.schemas import (
    ModificationRequest, ModificationProposal, AuthorizationRecord,
    ModificationResult, RollbackRecord, PatchPayload, FilePatch,
    FileOperationType, ModificationMode, ApprovalStatus, RollbackStatus,
    WRITE_AUTHORIZATION_TTL_SECONDS,
)
from modification.errors import (
    ModificationError,
    PROPOSAL_NOT_FOUND,
    MODIFICATION_NOT_FOUND,
    WORKSPACE_NOT_AUTHORIZED,
    BLOCKED_REQUIRES_PERMISSION,
    MODIFICATION_FAILED,
)
from modification.validator import PatchValidator
from modification.atomic import AtomicPatcher, acquire_deterministic_locks
from modification.backup import BackupManager
from modification.verifier import PostWriteVerifier
from modification.diff_parser import DiffParser
from modification.audit import log_modification_audit
from modification.stores import (
    ProposalStore, ModificationStore, AuthorizationStore, RollbackStore
)
from utils.logger import logger


class ModificationOrchestrator:
    """Core orchestration engine for controlled code modifications."""

    def __init__(
        self,
        ws_store: Optional[WorkspaceStore] = None,
        proposal_store: Optional[ProposalStore] = None,
        mod_store: Optional[ModificationStore] = None,
        auth_store: Optional[AuthorizationStore] = None,
        roll_store: Optional[RollbackStore] = None,
    ):
        self._ws_store       = ws_store or WorkspaceStore()
        self._proposal_store = proposal_store or ProposalStore()
        self._mod_store      = mod_store or ModificationStore()
        self._auth_store     = auth_store or AuthorizationStore()
        self._roll_store     = roll_store or RollbackStore()
        self._validator      = PatchValidator(
            ws_store=self._ws_store,
            auth_store=self._auth_store,
        )
        self._backup_mgr     = BackupManager(self._roll_store)

    # ------------------------------------------------------------------
    # Stage 1: PROPOSE (Zero Mutations)
    # ------------------------------------------------------------------

    def propose(self, request: ModificationRequest) -> ModificationProposal:
        """
        Validates proposal and saves it in the proposal store.
        Performs ZERO mutations on disk.
        """
        start_time = time.perf_counter()
        proposal_id = f"prop_{uuid.uuid4().hex[:10]}"

        # 1. Validate full proposal schema, paths, limits, sensitive rules
        ws_root, affected_files, warnings, adds, dels, mods = self._validator.validate_proposal(
            workspace_id=request.workspace_id,
            patch_payload=request.patch,
            plan_id=request.plan_id,
            execution_id=request.execution_id,
            task_id=request.task_id,
        )

        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=WRITE_AUTHORIZATION_TTL_SECONDS)).isoformat().replace("+00:00", "Z")

        proposal = ModificationProposal(
            proposal_id=proposal_id,
            workspace_id=request.workspace_id,
            plan_id=request.plan_id,
            execution_id=request.execution_id,
            task_id=request.task_id,
            files_affected=affected_files,
            patch=request.patch,
            additions=adds,
            deletions=dels,
            modifications=mods,
            risk_level="HIGH" if dels > 0 or len(affected_files) > 5 else "MEDIUM",
            required_permission="WRITE",
            sensitive_files=[],
            validation_status="VALID",
            warnings=warnings,
            created_at=now.isoformat().replace("+00:00", "Z"),
            expires_at=expires_at,
        )

        self._proposal_store.save_item(proposal_id, proposal.model_dump())

        duration_ms = (time.perf_counter() - start_time) * 1000
        log_modification_audit(
            proposal_id=proposal_id,
            request_id=request.request_id,
            workspace_id=request.workspace_id,
            plan_id=request.plan_id,
            execution_id=request.execution_id,
            task_id=request.task_id,
            operation="PROPOSE",
            status="PROPOSED",
            files_count=len(affected_files),
            duration_ms=duration_ms,
        )

        return proposal

    # ------------------------------------------------------------------
    # Stage 2: PREVIEW (Zero Mutations)
    # ------------------------------------------------------------------

    def preview(self, proposal_id: str) -> ModificationProposal:
        """
        Loads proposal and re-evaluates validation against current disk state.
        Performs ZERO mutations on disk.
        """
        prop_data = self._proposal_store.get_item(proposal_id)
        if not prop_data:
            raise ModificationError(PROPOSAL_NOT_FOUND, f"Proposal '{proposal_id}' not found.")

        proposal = ModificationProposal(**prop_data)
        # Re-validate against disk
        self._validator.validate_proposal(
            workspace_id=proposal.workspace_id,
            patch_payload=proposal.patch,
            plan_id=proposal.plan_id,
            execution_id=proposal.execution_id,
            task_id=proposal.task_id,
        )

        log_modification_audit(
            proposal_id=proposal_id,
            workspace_id=proposal.workspace_id,
            operation="PREVIEW",
            status="VALID",
            files_count=len(proposal.files_affected),
        )

        return proposal

    # ------------------------------------------------------------------
    # Authorization: APPROVE (Issues Server-Side Token)
    # ------------------------------------------------------------------

    def approve(
        self,
        proposal_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> AuthorizationRecord:
        """
        Generates and persists a server-side authorization grant for a proposal.
        """
        prop_data = self._proposal_store.get_item(proposal_id)
        if not prop_data:
            raise ModificationError(PROPOSAL_NOT_FOUND, f"Proposal '{proposal_id}' not found.")

        proposal = ModificationProposal(**prop_data)
        auth_id = f"auth_write_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=WRITE_AUTHORIZATION_TTL_SECONDS)).isoformat().replace("+00:00", "Z")

        auth_record = AuthorizationRecord(
            authorization_id=auth_id,
            workspace_id=proposal.workspace_id,
            plan_id=proposal.plan_id,
            execution_id=proposal.execution_id,
            task_id=proposal.task_id,
            proposal_id=proposal_id,
            authorized_permission="WRITE",
            authorized_at=now.isoformat().replace("+00:00", "Z"),
            expires_at=expires_at,
            status=ApprovalStatus.APPROVED,
            user_id=user_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )

        self._auth_store.save_item(auth_id, auth_record.model_dump())

        log_modification_audit(
            proposal_id=proposal_id,
            authorization_id=auth_id,
            workspace_id=proposal.workspace_id,
            operation="APPROVE",
            status="APPROVED",
            permission="WRITE",
        )

        return auth_record

    # ------------------------------------------------------------------
    # Stage 3: APPLY (Atomic Patch Application with Rollback Snapshot)
    # ------------------------------------------------------------------

    def apply(
        self,
        proposal_id: str,
        authorization_id: str,
    ) -> ModificationResult:
        """
        Applies an authorized modification proposal atomically.
        """
        start_time = time.perf_counter()
        modification_id = f"mod_{uuid.uuid4().hex[:10]}"

        # 1. Load Proposal
        prop_data = self._proposal_store.get_item(proposal_id)
        if not prop_data:
            raise ModificationError(PROPOSAL_NOT_FOUND, f"Proposal '{proposal_id}' not found.")
        proposal = ModificationProposal(**prop_data)

        # 2. Validate Workspace
        ws_data = self._ws_store.get_workspace(proposal.workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Workspace is not authorized.")
        workspace_root = ws_data["root_path"]

        # 3. Validate Authorization
        self._validator.validate_apply_authorization(
            workspace_id=proposal.workspace_id,
            proposal_id=proposal_id,
            authorization_id=authorization_id,
        )

        # 4. Resolve canonical paths and acquire deterministic locks
        canonical_paths: List[str] = []
        for p in proposal.patch.patches:
            canonical_paths.append(verify_safe_path(workspace_root, p.path))
            if p.operation == FileOperationType.RENAME and p.new_path:
                canonical_paths.append(verify_safe_path(workspace_root, p.new_path))

        with acquire_deterministic_locks(canonical_paths):
            # 5. Take pre-write snapshot for rollback
            rollback_record = self._backup_mgr.create_pre_write_snapshot(
                workspace_root=workspace_root,
                modification_id=modification_id,
                workspace_id=proposal.workspace_id,
                patches=proposal.patch.patches,
            )

            # 6. Execute atomic patches
            files_changed: List[str] = []
            files_created: List[str] = []
            files_deleted: List[str] = []
            bytes_written_total = 0
            new_hashes: Dict[str, str] = {}

            try:
                for patch in proposal.patch.patches:
                    target_can, new_hash, b_written = AtomicPatcher.apply_single_patch_atomic(
                        workspace_root=workspace_root,
                        patch=patch,
                    )
                    bytes_written_total += b_written

                    if patch.operation == FileOperationType.CREATE:
                        files_created.append(patch.path)
                        new_hashes[patch.path] = new_hash or ""
                    elif patch.operation == FileOperationType.DELETE:
                        files_deleted.append(patch.path)
                        new_hashes[patch.path] = ""
                    elif patch.operation == FileOperationType.RENAME:
                        files_changed.append(patch.new_path or patch.path)
                        if patch.new_path:
                            new_hashes[patch.new_path] = new_hash or ""
                    else:  # MODIFY
                        files_changed.append(patch.path)
                        new_hashes[patch.path] = new_hash or ""

                # 7. Update rollback record with new hashes
                self._backup_mgr.update_post_write_hashes(rollback_record.rollback_id, new_hashes)

                # 8. Post-write read-only verification
                verification = PostWriteVerifier.verify_patch_results(
                    workspace_root=workspace_root,
                    patches=proposal.patch.patches,
                    expected_hashes=new_hashes,
                )

                # 9. Mark authorization as CONSUMED
                auth_data = self._auth_store.get_item(authorization_id)
                if auth_data:
                    auth_data["status"] = "CONSUMED"
                    self._auth_store.save_item(authorization_id, auth_data)

                # 10. Assemble and save ModificationResult
                audit_ref = log_modification_audit(
                    modification_id=modification_id,
                    proposal_id=proposal_id,
                    authorization_id=authorization_id,
                    workspace_id=proposal.workspace_id,
                    plan_id=proposal.plan_id,
                    execution_id=proposal.execution_id,
                    task_id=proposal.task_id,
                    operation="APPLY",
                    status="APPLIED",
                    files_count=len(files_changed) + len(files_created) + len(files_deleted),
                    bytes_written=bytes_written_total,
                    duration_ms=(time.perf_counter() - start_time) * 1000,
                )

                result = ModificationResult(
                    modification_id=modification_id,
                    proposal_id=proposal_id,
                    workspace_id=proposal.workspace_id,
                    status="APPLIED",
                    files_changed=files_changed,
                    files_created=files_created,
                    files_deleted=files_deleted,
                    bytes_written=bytes_written_total,
                    verification=verification,
                    rollback_available=True,
                    rollback_id=rollback_record.rollback_id,
                    audit_reference=audit_ref,
                    created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                )

                self._mod_store.save_item(modification_id, result.model_dump())
                return result

            except Exception as e:
                # Attempt immediate automatic rollback on mid-operation failure
                logger.error(f"[orchestrator] Error during patch application: {e}. Initiating rollback.")
                try:
                    self._backup_mgr.execute_rollback(workspace_root, modification_id)
                except Exception as rb_err:
                    logger.error(f"[orchestrator] Rollback following failure also encountered error: {rb_err}")

                if isinstance(e, ModificationError):
                    raise e
                raise ModificationError(MODIFICATION_FAILED, f"Patch application failed: {e}")

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    def rollback(self, modification_id: str) -> ModificationResult:
        """
        Restores workspace to pre-modification state using the recorded snapshot.
        """
        mod_data = self._mod_store.get_item(modification_id)
        if not mod_data:
            raise ModificationError(MODIFICATION_NOT_FOUND, f"Modification '{modification_id}' not found.")

        workspace_id = mod_data.get("workspace_id", "")
        ws_data = self._ws_store.get_workspace(workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Workspace is not authorized.")
        workspace_root = ws_data["root_path"]

        # Execute rollback
        rollback_record = self._backup_mgr.execute_rollback(workspace_root, modification_id)

        # Update modification record
        mod_data["status"] = "ROLLBACK_COMPLETED"
        mod_data["rollback_available"] = False
        self._mod_store.save_item(modification_id, mod_data)

        log_modification_audit(
            modification_id=modification_id,
            workspace_id=workspace_id,
            operation="ROLLBACK",
            status="ROLLBACK_COMPLETED",
            files_count=len(rollback_record.affected_files),
        )

        return ModificationResult(**mod_data)

    # ------------------------------------------------------------------
    # Diff View
    # ------------------------------------------------------------------

    def get_diff(self, proposal_id: str) -> Dict[str, Any]:
        """
        Renders sanitized diff preview for all files in a proposal.
        """
        prop_data = self._proposal_store.get_item(proposal_id)
        if not prop_data:
            raise ModificationError(PROPOSAL_NOT_FOUND, f"Proposal '{proposal_id}' not found.")

        proposal = ModificationProposal(**prop_data)
        ws_data = self._ws_store.get_workspace(proposal.workspace_id)
        if not ws_data:
            raise ModificationError(WORKSPACE_NOT_AUTHORIZED, "Workspace not authorized.")
        workspace_root = ws_data["root_path"]

        diffs: Dict[str, str] = {}
        for p in proposal.patch.patches:
            canonical = verify_safe_path(workspace_root, p.path)
            _, orig_text, _ = AtomicPatcher.read_file_safe(canonical, p.encoding)
            orig_text = orig_text or ""
            new_text = DiffParser.apply_patch_to_text(orig_text, p)
            diffs[p.path] = DiffParser.generate_unified_diff(orig_text, new_text, p.path)

        return {
            "proposal_id": proposal_id,
            "workspace_id": proposal.workspace_id,
            "diffs": diffs,
            "additions": proposal.additions,
            "deletions": proposal.deletions,
            "modifications": proposal.modifications,
        }
