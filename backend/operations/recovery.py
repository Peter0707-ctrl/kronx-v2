"""
Phase 3.1 — Safe Recovery Engine
Orchestrates validated, hash-verified, atomic restoration of persistent JSON stores.
Fails closed on hash mismatch, corrupt backup, or invalid store target.
"""
import os
import json
import shutil
import tempfile
from typing import Optional
from datetime import datetime, timezone

from operations.schemas import RecoveryResult, RecoveryRequest
from operations.errors import (
    OperationsError,
    BACKUP_NOT_FOUND,
    RECOVERY_BLOCKED,
    RECOVERY_FAILED,
    UNAUTHORIZED_OPERATION,
)
from operations.store import OperationsStore
from operations.integrity import KNOWN_STORES, StoreIntegrityManager
from operations.audit import log_operations_audit
from utils.logger import logger

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(BACKEND_DIR, "backups")


class RecoveryEngine:
    def __init__(
        self,
        base_dir: Optional[str] = None,
        backup_dir: Optional[str] = None,
        store: Optional[OperationsStore] = None
    ):
        self.base_dir = base_dir or BACKEND_DIR
        self.backup_dir = backup_dir or BACKUP_DIR
        self._store = store or OperationsStore()
        self._integrity = StoreIntegrityManager(self.base_dir)

    def restore_backup(self, request: RecoveryRequest, operator_role: str = "OPERATOR") -> RecoveryResult:
        """
        Executes atomic, verified recovery from a recorded backup.
        Enforces:
        - Must be an approved store
        - Backup record must exist
        - Backup file SHA-256 must match recorded hash
        - Restored JSON structure must parse correctly
        """
        # 1. Authorization check
        if operator_role not in ["OPERATOR", "ADMIN", "OWNER"]:
            raise OperationsError(
                UNAUTHORIZED_OPERATION,
                f"Role '{operator_role}' is not authorized to restore system backups.",
                status_code=403,
            )

        # 2. Approved store check
        clean_store = os.path.basename(request.store_name)
        if clean_store not in KNOWN_STORES:
            raise OperationsError(
                UNAUTHORIZED_OPERATION,
                f"Target store '{clean_store}' is not an approved Kron-X persistent store.",
                status_code=400,
            )

        # 3. Lookup backup metadata
        b_meta = self._store.get_backup(request.backup_id)
        if not b_meta:
            raise OperationsError(
                BACKUP_NOT_FOUND,
                f"Backup record '{request.backup_id}' not found.",
                status_code=404,
            )

        backup_file = os.path.join(self.backup_dir, b_meta.get("backup_filename", ""))
        if not os.path.exists(backup_file):
            raise OperationsError(
                BACKUP_NOT_FOUND,
                f"Backup file for '{request.backup_id}' does not exist on disk.",
                status_code=404,
            )

        # 4. Hash verification (detect tampering or corruption)
        actual_hash = self._integrity.compute_sha256(backup_file)
        expected_hash = b_meta.get("sha256", "")
        if actual_hash != expected_hash:
            logger.error(f"[recovery] Hash mismatch for backup '{request.backup_id}'. Expected {expected_hash}, got {actual_hash}")
            raise OperationsError(
                RECOVERY_BLOCKED,
                "Backup integrity verification failed (SHA-256 hash mismatch). Recovery blocked.",
                status_code=400,
            )

        # 5. Atomic restore
        target_path = os.path.join(self.base_dir, clean_store)
        fd, tmp_restore = tempfile.mkstemp(dir=self.base_dir, prefix="rec_tmp_")
        try:
            os.close(fd)
            shutil.copy2(backup_file, tmp_restore)

            # Pre-validate target JSON syntax
            with open(tmp_restore, "r", encoding="utf-8") as f:
                parsed_data = json.load(f)
                restored_count = len(parsed_data) if isinstance(parsed_data, (dict, list)) else 1

            shutil.move(tmp_restore, target_path)

            # 6. Post-restore health verification
            integrity_check = self._integrity.check_store(clean_store)
            if integrity_check.corrupted:
                raise OperationsError(
                    RECOVERY_FAILED,
                    f"Restored store '{clean_store}' failed integrity check: {integrity_check.error_message}",
                    status_code=500,
                )

            res = RecoveryResult(
                status="SUCCESS",
                backup_id=request.backup_id,
                store_name=clean_store,
                restored_records=restored_count,
                verification_passed=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            log_operations_audit(
                action="RECOVERY_RESTORED",
                status="SUCCESS",
                details={
                    "backup_id": request.backup_id,
                    "store_name": clean_store,
                    "restored_records": restored_count,
                }
            )
            return res

        except Exception as e:
            if os.path.exists(tmp_restore):
                try:
                    os.remove(tmp_restore)
                except Exception:
                    pass
            if isinstance(e, OperationsError):
                raise e
            logger.error(f"[recovery] Recovery restore error: {e}")
            raise OperationsError(
                RECOVERY_FAILED,
                f"Failed to restore backup: {str(e)[:100]}",
                status_code=500,
            )
