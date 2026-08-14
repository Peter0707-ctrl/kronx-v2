"""
Phase 2F — Verification Store
Thread-safe atomic file persistence for verification results with corruption recovery and mtime invalidation.
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
from verification.schemas import MAX_STORED_VERIFICATIONS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFICATION_STORE_FILE = os.path.join(BASE_DIR, "verification_store.json")

_store_lock = threading.RLock()


class VerificationStore:
    """Store for persisting verification records safely."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or VERIFICATION_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"verifications": {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[verification_store] Failed to create {self.path}: {e}")

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
            self._cache = {"verifications": {}}
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
            logger.error(f"[verification_store] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[verification_store] Saved corrupted store to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[verification_store] Failed to backup corrupted store: {be}")
            self._cache = {"verifications": {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as we:
                logger.error(f"[verification_store] Failed to write fresh store file: {we}")
        except Exception as e:
            logger.error(f"[verification_store] Failed to load {self.path}: {e}")
            self._cache = {"verifications": {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="ver_store_tmp_", suffix=".json"
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
            logger.error(f"[verification_store] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def get_verification(self, verification_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("verifications", {}).get(verification_id)

    def save_verification(self, verification_id: str, verification_data: dict):
        with _store_lock:
            data = self._load_under_lock()
            verifications = data.get("verifications", {})
            verifications[verification_id] = verification_data

            if len(verifications) > MAX_STORED_VERIFICATIONS:
                sorted_keys = sorted(
                    verifications.keys(),
                    key=lambda k: verifications[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(verifications) - MAX_STORED_VERIFICATIONS]:
                    del verifications[old_key]

            data["verifications"] = verifications
            self._save_under_lock(data)
