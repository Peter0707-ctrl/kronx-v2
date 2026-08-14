import json
import os
import threading
import shutil
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import logger

WORKSPACE_STORE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workspace_store.json")
_store_lock = threading.Lock()

class WorkspaceStore:
    def __init__(self):
        self.path = WORKSPACE_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()


    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"workspaces": {}, "jobs": {}}, f)
                except Exception as e:
                    logger.error(f"Failed to create workspace store file: {e}", exc_info=True)

    def _load_under_lock(self) -> dict:
        # Invalidate in-memory cache if the file has been modified by another instance
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
            self._cache = {"workspaces": {}, "jobs": {}}
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
            logger.error(f"Workspace store JSON corrupted: {jde}", exc_info=True)
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                if os.path.exists(self.path):
                    shutil.copy2(self.path, corrupt_backup)
                    logger.warning(f"Saved corrupted workspace file to {corrupt_backup}")
            except Exception as backup_err:
                logger.error(f"Failed to backup corrupted file: {backup_err}", exc_info=True)

            self._cache = {"workspaces": {}, "jobs": {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as write_err:
                logger.error(f"Failed to write fresh file during recovery: {write_err}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to load workspace store: {e}", exc_info=True)
            self._cache = {"workspaces": {}, "jobs": {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix="workspace_store_tmp_", suffix=".json")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, default=str)
                f.flush()
                try:
                    os.fsync(temp_fd)
                except Exception:
                    pass
            os.replace(temp_path, self.path)
            # Update mtime so this instance doesn't self-invalidate
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except Exception as e:
            logger.error(f"Failed to save workspace store atomically: {e}", exc_info=True)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


    def get_workspace(self, workspace_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("workspaces", {}).get(workspace_id)

    def save_workspace(self, workspace_id: str, workspace_data: dict):
        with _store_lock:
            data = self._load_under_lock()
            if "workspaces" not in data:
                data["workspaces"] = {}
            data["workspaces"][workspace_id] = workspace_data
            self._save_under_lock(data)

    def delete_workspace(self, workspace_id: str):
        with _store_lock:
            data = self._load_under_lock()
            if "workspaces" in data and workspace_id in data["workspaces"]:
                del data["workspaces"][workspace_id]
                self._save_under_lock(data)

    def get_job(self, job_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("jobs", {}).get(job_id)

    def save_job(self, job_id: str, job_data: dict):
        with _store_lock:
            data = self._load_under_lock()
            if "jobs" not in data:
                data["jobs"] = {}
            data["jobs"][job_id] = job_data
            self._save_under_lock(data)
