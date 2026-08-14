"""
Phase 2D — Execution Store & Checkpointing
Atomic, thread-safe persistence for execution records and checkpoints.
Uses tempfile + os.replace with mtime-based cross-instance cache invalidation and corruption recovery.
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

EXECUTION_STORE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "execution_store.json"
)

_store_lock = threading.Lock()

MAX_STORED_EXECUTIONS = 500


class ExecutionStore:
    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or EXECUTION_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"executions": {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[execution_store] Failed to create store file: {e}")

    def _load_under_lock(self) -> dict:
        # Invalidate cache if file was modified on disk by another instance
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
            self._cache = {"executions": {}}
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
            logger.error(f"[execution_store] JSON corrupted: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[execution_store] Saved corrupted file to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[execution_store] Failed to backup corrupted file: {be}")
            self._cache = {"executions": {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as we:
                logger.error(f"[execution_store] Failed to write fresh file during recovery: {we}")
        except Exception as e:
            logger.error(f"[execution_store] Failed to load store: {e}")
            self._cache = {"executions": {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="exec_store_tmp_", suffix=".json"
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
            logger.error(f"[execution_store] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_execution(self, execution_id: str, execution_data: dict):
        """Save execution record, pruning oldest entries if limit exceeded."""
        with _store_lock:
            data = self._load_under_lock()
            executions = data.get("executions", {})
            executions[execution_id] = execution_data
            
            # Prune oldest if limit exceeded
            if len(executions) > MAX_STORED_EXECUTIONS:
                sorted_keys = sorted(
                    executions.keys(),
                    key=lambda k: executions[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(executions) - MAX_STORED_EXECUTIONS]:
                    del executions[old_key]

            data["executions"] = executions
            self._save_under_lock(data)

    def get_execution(self, execution_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("executions", {}).get(execution_id)

    def list_executions_for_workspace(self, workspace_id: str) -> List[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return [
                v for v in data.get("executions", {}).values()
                if v.get("workspace_id") == workspace_id
            ]
