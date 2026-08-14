"""
Phase 2E — Pre-Write Snapshot & Safe Rollback Engine
Captures original file contents and hashes prior to modification.
Executes atomic rollbacks with conflict detection against concurrent or external changes.
"""
from __future__ import annotations
import os
import uuid
from typing import Dict, List, Optional, Tuple, Any

from tools.path_verify import verify_safe_path
from modification.schemas import (
    FilePatch, FileOperationType, RollbackRecord, RollbackStatus
)
from modification.atomic import AtomicPatcher, acquire_deterministic_locks
from modification.stores import RollbackStore
from modification.errors import (
    ModificationError,
    ROLLBACK_CONFLICT,
    ROLLBACK_FAILED,
    MODIFICATION_NOT_FOUND,
)
from utils.logger import logger


class BackupManager:
    """Manages pre-modification backups and safe rollback operations."""

    def __init__(self, rollback_store: Optional[RollbackStore] = None):
        self._store = rollback_store or RollbackStore()

    def create_pre_write_snapshot(
        self,
        workspace_root: str,
        modification_id: str,
        workspace_id: str,
        patches: List[FilePatch],
    ) -> RollbackRecord:
        """
        Takes snapshot of all files before modification.
        Stores previous contents and hashes in a RollbackRecord.
        """
        rollback_id = f"roll_{uuid.uuid4().hex[:10]}"
        affected_files: List[str] = []
        previous_hashes: Dict[str, str] = {}
        backups: Dict[str, Optional[str]] = {}

        for p in patches:
            affected_files.append(p.path)
            canonical = verify_safe_path(workspace_root, p.path)
            exists, content, f_hash = AtomicPatcher.read_file_safe(canonical, p.encoding)
            
            if exists and content is not None and f_hash is not None:
                previous_hashes[p.path] = f_hash
                backups[p.path] = content
            else:
                previous_hashes[p.path] = ""
                backups[p.path] = None  # Did not exist before (e.g. CREATE operation)

            # If rename, record destination if exists
            if p.operation == FileOperationType.RENAME and p.new_path:
                affected_files.append(p.new_path)
                can_dest = verify_safe_path(workspace_root, p.new_path)
                d_exists, d_content, d_hash = AtomicPatcher.read_file_safe(can_dest, p.encoding)
                if d_exists and d_content is not None and d_hash is not None:
                    previous_hashes[p.new_path] = d_hash
                    backups[p.new_path] = d_content
                else:
                    previous_hashes[p.new_path] = ""
                    backups[p.new_path] = None

        record = RollbackRecord(
            rollback_id=rollback_id,
            modification_id=modification_id,
            workspace_id=workspace_id,
            affected_files=affected_files,
            previous_hashes=previous_hashes,
            new_hashes={},  # To be populated after successful write
            backups=backups,
            status=RollbackStatus.AVAILABLE,
        )
        self._store.save_item(rollback_id, record.model_dump())
        return record

    def update_post_write_hashes(self, rollback_id: str, new_hashes: Dict[str, str]):
        """Updates rollback record with the newly generated hashes post-write."""
        data = self._store.get_item(rollback_id)
        if data:
            data["new_hashes"] = new_hashes
            self._store.save_item(rollback_id, data)

    def execute_rollback(
        self,
        workspace_root: str,
        modification_id: str,
    ) -> RollbackRecord:
        """
        Rollback all changes associated with modification_id.
        Verifies that current disk state matches post-write hashes before restoring.
        """
        # Find rollback record by modification_id
        rollback_data = None
        for record_dict in self._store._load_under_lock().get("rollbacks", {}).values():
            if record_dict.get("modification_id") == modification_id:
                rollback_data = record_dict
                break

        if not rollback_data:
            raise ModificationError(MODIFICATION_NOT_FOUND, f"No rollback record found for modification '{modification_id}'.")

        record = RollbackRecord(**rollback_data)
        if record.status != RollbackStatus.AVAILABLE:
            raise ModificationError(ROLLBACK_FAILED, f"Rollback '{record.rollback_id}' status is '{record.status}'.")

        # 1. Resolve canonical paths for locking
        canonical_paths = [verify_safe_path(workspace_root, p) for p in record.affected_files]

        with acquire_deterministic_locks(canonical_paths):
            # 2. Check for conflicts: current state must match new_hashes (if recorded)
            for rel_path, expected_new_hash in record.new_hashes.items():
                can_p = verify_safe_path(workspace_root, rel_path)
                current_h = AtomicPatcher.get_file_sha256(can_p) or ""
                if current_h != expected_new_hash:
                    record.status = RollbackStatus.CONFLICT
                    self._store.save_item(record.rollback_id, record.model_dump())
                    raise ModificationError(
                        ROLLBACK_CONFLICT,
                        f"File '{rel_path}' has been modified since the patch was applied (current hash differs)."
                    )

            # 3. Atomically restore original states
            try:
                for rel_path, original_content in record.backups.items():
                    can_p = verify_safe_path(workspace_root, rel_path)
                    if original_content is None:
                        # File did not exist before -> remove if currently exists
                        if os.path.exists(can_p):
                            os.remove(can_p)
                    else:
                        # Restore original content atomically
                        AtomicPatcher._write_file_atomically(can_p, original_content)

                record.status = RollbackStatus.APPLIED
                self._store.save_item(record.rollback_id, record.model_dump())
                logger.info(f"[rollback] Successfully rolled back modification '{modification_id}'")
                return record
            except ModificationError:
                raise
            except Exception as e:
                logger.error(f"[rollback] Error during rollback of '{modification_id}': {e}")
                record.status = RollbackStatus.CONFLICT
                self._store.save_item(record.rollback_id, record.model_dump())
                raise ModificationError(ROLLBACK_FAILED, f"Rollback execution failed: {e}")
