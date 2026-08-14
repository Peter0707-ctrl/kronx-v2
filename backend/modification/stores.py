"""
Phase 2E — Atomic Persistence Stores for Modifications, Authorizations, and Rollbacks
Uses tempfile + os.replace with mtime-based cache invalidation and corruption recovery.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODIFICATION_STORE_FILE  = os.path.join(BASE_DIR, "modification_store.json")
AUTHORIZATION_STORE_FILE = os.path.join(BASE_DIR, "authorization_store.json")
ROLLBACK_STORE_FILE      = os.path.join(BASE_DIR, "rollback_store.json")

_store_lock = threading.RLock()
MAX_STORED_RECORDS = 500



class BaseAtomicStore:
    """Base class for thread-safe atomic JSON file persistence."""

    def __init__(self, file_path: str, root_key: str):
        self.path = file_path
        self.root_key = root_key
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({self.root_key: {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[store] Failed to create {self.path}: {e}")

    def _load_under_lock(self) -> dict:
        if self._cache is not None and os.path.exists(self.path):
            try:
                mtime = os.path.getmtime(self.path)
                if mtime > self._cache_mtime:
                    self._cache = None
            except Exception:
                pass

        if self._cache is not None:
            return json.loads(json.dumps(self._cache))

        if not os.path.exists(self.path):
            self._cache = {self.root_key: {}}
            self._cache_mtime = 0
            return self._cache

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except json.JSONDecodeError as jde:
            logger.error(f"[store] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[store] Saved corrupted store to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[store] Failed to backup corrupted store: {be}")
            self._cache = {self.root_key: {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as we:
                logger.error(f"[store] Failed to write fresh store file: {we}")
        except Exception as e:
            logger.error(f"[store] Failed to load {self.path}: {e}")
            self._cache = {self.root_key: {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="store_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
                f.flush()
                try:
                    os.fsync(temp_fd)
                except Exception:
                    pass
            os.replace(temp_path, self.path)
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except Exception as e:
            logger.error(f"[store] Atomic save failed for {self.path}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def get_item(self, key: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get(self.root_key, {}).get(key)

    def save_item(self, key: str, value: dict):
        with _store_lock:
            data = self._load_under_lock()
            items = data.get(self.root_key, {})
            items[key] = value

            if len(items) > MAX_STORED_RECORDS:
                sorted_keys = sorted(
                    items.keys(),
                    key=lambda k: items[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(items) - MAX_STORED_RECORDS]:
                    del items[old_key]

            data[self.root_key] = items
            self._save_under_lock(data)

    def delete_item(self, key: str):
        with _store_lock:
            data = self._load_under_lock()
            items = data.get(self.root_key, {})
            if key in items:
                del items[key]
                data[self.root_key] = items
                self._save_under_lock(data)


# ------------------------------------------------------------------
# Concrete Stores
# ------------------------------------------------------------------

class ModificationStore(BaseAtomicStore):
    def __init__(self, store_path: Optional[str] = None):
        super().__init__(store_path or MODIFICATION_STORE_FILE, "modifications")


class ProposalStore(BaseAtomicStore):
    def __init__(self, store_path: Optional[str] = None):
        super().__init__(store_path or os.path.join(BASE_DIR, "proposal_store.json"), "proposals")


class AuthorizationStore(BaseAtomicStore):
    def __init__(self, store_path: Optional[str] = None):
        super().__init__(store_path or AUTHORIZATION_STORE_FILE, "authorizations")


class RollbackStore(BaseAtomicStore):
    def __init__(self, store_path: Optional[str] = None):
        super().__init__(store_path or ROLLBACK_STORE_FILE, "rollbacks")
