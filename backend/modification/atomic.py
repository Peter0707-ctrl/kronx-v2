"""
Phase 2E — Atomic File Patcher & Concurrency Engine
Executes atomic file operations (CREATE, MODIFY, DELETE, RENAME) using temporary files + os.replace.
Enforces optimistic hash verification and deterministic multi-file locking to prevent deadlocks and race conditions.
"""
from __future__ import annotations
import os
import hashlib
import tempfile
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple, Set

from tools.path_verify import verify_safe_path
from modification.schemas import FilePatch, FileOperationType
from modification.diff_parser import DiffParser
from modification.errors import (
    ModificationError,
    FILE_STATE_CHANGED,
    FILE_ALREADY_EXISTS,
    FILE_NOT_FOUND,
    PATH_OUTSIDE_WORKSPACE,
    MODIFICATION_FAILED,
)
from utils.logger import logger

_global_file_locks: Dict[str, threading.RLock] = {}
_lock_registry_lock = threading.RLock()


def _get_file_lock(canonical_path: str) -> threading.RLock:
    with _lock_registry_lock:
        if canonical_path not in _global_file_locks:
            _global_file_locks[canonical_path] = threading.RLock()
        return _global_file_locks[canonical_path]



@contextmanager
def acquire_deterministic_locks(canonical_paths: List[str]):
    """
    Acquire locks in sorted lexicographical order to avoid deadlocks across multiple files.
    """
    sorted_paths = sorted(list(set(canonical_paths)))
    acquired_locks = []
    try:
        for p in sorted_paths:
            lock = _get_file_lock(p)
            lock.acquire()
            acquired_locks.append(lock)
        yield
    finally:
        for lock in reversed(acquired_locks):
            try:
                lock.release()
            except Exception:
                pass


def compute_sha256(content: bytes) -> str:
    """Computes standard sha256 hex digest for binary content."""
    return hashlib.sha256(content).hexdigest()


class AtomicPatcher:
    """Engine for atomic file modification, creation, deletion, and renaming."""

    @staticmethod
    def get_file_sha256(file_path: str) -> Optional[str]:
        """Returns sha256 of file if it exists, otherwise None."""
        if not os.path.isfile(file_path):
            return None
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None

    @staticmethod
    def read_file_safe(file_path: str, encoding: str = "utf-8") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Reads file safely, returning (exists, text_content, sha256).
        """
        if not os.path.exists(file_path):
            return False, None, None
        try:
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
                file_hash = hashlib.sha256(raw_bytes).hexdigest()
                text = raw_bytes.decode(encoding, errors="replace")
                return True, text, file_hash
        except Exception as e:
            logger.error(f"[atomic_patcher] Error reading {file_path}: {e}")
            return False, None, None

    @staticmethod
    def apply_single_patch_atomic(
        workspace_root: str,
        patch: FilePatch,
    ) -> Tuple[str, Optional[str], int]:
        """
        Applies a single FilePatch atomically.
        Returns (target_canonical_path, new_sha256, bytes_written).
        Raises ModificationError on verification or atomic write failure.
        """
        # 1. Resolve and verify containment
        canonical_target = verify_safe_path(workspace_root, patch.path)

        exists, current_text, current_hash = AtomicPatcher.read_file_safe(canonical_target, patch.encoding)

        # 2. Pre-condition checks based on operation
        if patch.operation == FileOperationType.CREATE:
            if exists:
                raise ModificationError(FILE_ALREADY_EXISTS, f"Cannot CREATE file '{patch.path}': already exists.")
            new_text = patch.new_content or ""
            return AtomicPatcher._write_file_atomically(canonical_target, new_text, patch.encoding)

        elif patch.operation == FileOperationType.MODIFY:
            if not exists:
                raise ModificationError(FILE_NOT_FOUND, f"Cannot MODIFY file '{patch.path}': file does not exist.")

            # Optimistic concurrency check
            if patch.expected_sha256 and current_hash != patch.expected_sha256:
                raise ModificationError(
                    FILE_STATE_CHANGED,
                    f"File '{patch.path}' state has changed (expected {patch.expected_sha256[:8]}, actual {current_hash[:8] if current_hash else 'none'})."
                )

            new_text = DiffParser.apply_patch_to_text(current_text or "", patch)
            return AtomicPatcher._write_file_atomically(canonical_target, new_text, patch.encoding)

        elif patch.operation == FileOperationType.DELETE:
            if not exists:
                raise ModificationError(FILE_NOT_FOUND, f"Cannot DELETE file '{patch.path}': file does not exist.")

            if patch.expected_sha256 and current_hash != patch.expected_sha256:
                raise ModificationError(
                    FILE_STATE_CHANGED,
                    f"File '{patch.path}' state has changed before deletion."
                )

            try:
                os.remove(canonical_target)
                return canonical_target, None, 0
            except Exception as e:
                raise ModificationError(MODIFICATION_FAILED, f"Failed to delete file '{patch.path}': {e}")

        elif patch.operation == FileOperationType.RENAME:
            if not exists:
                raise ModificationError(FILE_NOT_FOUND, f"Cannot RENAME file '{patch.path}': source does not exist.")
            if not patch.new_path:
                raise ModificationError(MODIFICATION_FAILED, "RENAME requires 'new_path'.")

            canonical_dest = verify_safe_path(workspace_root, patch.new_path)
            if os.path.exists(canonical_dest):
                raise ModificationError(FILE_ALREADY_EXISTS, f"Cannot RENAME to '{patch.new_path}': destination already exists.")

            if patch.expected_sha256 and current_hash != patch.expected_sha256:
                raise ModificationError(FILE_STATE_CHANGED, f"Source file '{patch.path}' has changed.")

            # Ensure parent directory of destination exists
            dest_dir = os.path.dirname(canonical_dest)
            os.makedirs(dest_dir, exist_ok=True)

            try:
                os.replace(canonical_target, canonical_dest)
                new_hash = AtomicPatcher.get_file_sha256(canonical_dest)
                return canonical_dest, new_hash, 0
            except Exception as e:
                raise ModificationError(MODIFICATION_FAILED, f"Failed to rename '{patch.path}' to '{patch.new_path}': {e}")

        raise ModificationError(MODIFICATION_FAILED, f"Unsupported operation '{patch.operation}'.")

    @staticmethod
    def _write_file_atomically(target_path: str, content: str, encoding: str = "utf-8") -> Tuple[str, str, int]:
        """
        Writes content to temporary file in the same directory, flushes, fsyncs, and replaces target atomically.
        """
        parent_dir = os.path.dirname(target_path)
        os.makedirs(parent_dir, exist_ok=True)

        raw_bytes = content.encode(encoding)
        bytes_written = len(raw_bytes)
        new_hash = compute_sha256(raw_bytes)

        temp_fd, temp_path = tempfile.mkstemp(
            dir=parent_dir,
            prefix=".kronx_patch_tmp_",
            suffix=".tmp"
        )
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(raw_bytes)
                f.flush()
                try:
                    os.fsync(temp_fd)
                except Exception:
                    pass
            os.replace(temp_path, target_path)
            return target_path, new_hash, bytes_written
        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise ModificationError(MODIFICATION_FAILED, f"Atomic write failed for '{target_path}': {e}")
