"""
Phase 2G — Authentication Store
Thread-safe atomic persistence for users and sessions with corruption recovery and mtime cache invalidation.
Never placed in user workspaces.
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
AUTH_STORE_FILE = os.path.join(BASE_DIR, "auth_store.json")

_store_lock = threading.RLock()
MAX_STORED_USERS = 500
MAX_STORED_SESSIONS = 2000


class AuthStore:
    """Persistent JSON storage for user identities and session records."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or AUTH_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"users": {}, "sessions": {}, "username_index": {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[auth_store] Failed to create {self.path}: {e}")

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
            self._cache = {"users": {}, "sessions": {}, "username_index": {}}
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
            logger.error(f"[auth_store] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[auth_store] Saved corrupted store to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[auth_store] Failed to backup corrupted store: {be}")
            self._cache = {"users": {}, "sessions": {}, "username_index": {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as we:
                logger.error(f"[auth_store] Failed to write fresh store file: {we}")
        except Exception as e:
            logger.error(f"[auth_store] Failed to load {self.path}: {e}")
            self._cache = {"users": {}, "sessions": {}, "username_index": {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="auth_store_tmp_", suffix=".json"
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
            logger.error(f"[auth_store] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # User Operations
    # ------------------------------------------------------------------

    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("users", {}).get(user_id)

    def get_user_by_username(self, username: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            norm = username.strip().lower()
            user_id = data.get("username_index", {}).get(norm)
            if user_id:
                return data.get("users", {}).get(user_id)
            return None

    def save_user(self, user_data: dict):
        with _store_lock:
            data = self._load_under_lock()
            user_id = user_data["user_id"]
            username = user_data["username"]
            norm = username.strip().lower()

            users = data.get("users", {})
            u_index = data.get("username_index", {})

            users[user_id] = user_data
            u_index[norm] = user_id

            # Bounded user count
            if len(users) > MAX_STORED_USERS:
                sorted_keys = sorted(
                    users.keys(),
                    key=lambda k: users[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(users) - MAX_STORED_USERS]:
                    old_u = users.pop(old_key, None)
                    if old_u:
                        u_index.pop(old_u.get("username", "").strip().lower(), None)

            data["users"] = users
            data["username_index"] = u_index
            self._save_under_lock(data)

    # ------------------------------------------------------------------
    # Session Operations
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("sessions", {}).get(session_id)

    def save_session(self, session_id: str, session_data: dict):
        with _store_lock:
            data = self._load_under_lock()
            sessions = data.get("sessions", {})
            sessions[session_id] = session_data

            # Bounded session count
            if len(sessions) > MAX_STORED_SESSIONS:
                sorted_keys = sorted(
                    sessions.keys(),
                    key=lambda k: sessions[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(sessions) - MAX_STORED_SESSIONS]:
                    del sessions[old_key]

            data["sessions"] = sessions
            self._save_under_lock(data)

    def delete_session(self, session_id: str):
        with _store_lock:
            data = self._load_under_lock()
            sessions = data.get("sessions", {})
            if session_id in sessions:
                del sessions[session_id]
                data["sessions"] = sessions
                self._save_under_lock(data)
