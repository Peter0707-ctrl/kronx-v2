"""
Phase 3.1 — Application-Level Backup Engine
Performs safe, atomic local backups of approved Kron-X JSON stores with SHA-256 validation.
Explicitly rejects backups of .env, private keys, session tokens, and unapproved arbitrary files.
"""
import os
import uuid
import shutil
import hashlib
import tempfile
from typing import Optional, List
from datetime import datetime, timezone

from operations.schemas import BackupRecord
from operations.errors import OperationsError, BACKUP_FAILED, UNAUTHORIZED_OPERATION
from operations.store import OperationsStore
from operations.integrity import KNOWN_STORES, StoreIntegrityManager
from operations.audit import log_operations_audit
from utils.logger import logger

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(BACKEND_DIR, "backups")


class BackupEngine:
    def __init__(self, base_dir: Optional[str] = None, backup_dir: Optional[str] = None, store: Optional[OperationsStore] = None):
        self.base_dir = base_dir or BACKEND_DIR
        self.backup_dir = backup_dir or BACKUP_DIR
        self._store = store or OperationsStore()
        self._integrity = StoreIntegrityManager(self.base_dir)
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, store_name: str, tenant_scope: Optional[str] = None) -> BackupRecord:
        """Creates an atomic SHA-256 verified backup of an approved store file."""
        # 1. Reject unapproved store names
        clean_name = os.path.basename(store_name)
        if clean_name not in KNOWN_STORES:
            raise OperationsError(
                UNAUTHORIZED_OPERATION,
                f"Store '{clean_name}' is not an approved Kron-X persistent store for backup."
            )

        src_path = os.path.join(self.base_dir, clean_name)
        if not os.path.exists(src_path):
            raise OperationsError(
                BACKUP_FAILED,
                f"Store '{clean_name}' does not exist on disk."
            )

        backup_id = f"bak_{uuid.uuid4().hex[:12]}"
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{clean_name}.{timestamp_str}.{backup_id}.bak"
        dest_path = os.path.join(self.backup_dir, dest_filename)

        fd, tmp_path = tempfile.mkstemp(dir=self.backup_dir, prefix="bak_tmp_")
        try:
            os.close(fd)
            shutil.copy2(src_path, tmp_path)
            shutil.move(tmp_path, dest_path)

            sha256 = self._integrity.compute_sha256(dest_path)
            size_bytes = os.path.getsize(dest_path)

            record = BackupRecord(
                backup_id=backup_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                store_name=clean_name,
                sha256=sha256,
                size_bytes=size_bytes,
                status="COMPLETED",
                tenant_scope=tenant_scope,
                backup_filename=dest_filename,
            )

            self._store.record_backup(record.model_dump())

            log_operations_audit(
                action="BACKUP_CREATED",
                status="SUCCESS",
                tenant_id=tenant_scope,
                details={"backup_id": backup_id, "store_name": clean_name, "sha256": sha256, "size": size_bytes}
            )
            return record

        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            logger.error(f"[backup_engine] Backup failed for '{clean_name}': {e}")
            raise OperationsError(BACKUP_FAILED, f"Backup creation failed: {str(e)[:100]}")

    def list_backups(self, store_name: Optional[str] = None) -> List[BackupRecord]:
        """Lists recorded backup snapshots."""
        raw_list = self._store.list_backups(store_name=store_name)
        return [BackupRecord(**b) for b in raw_list]
