"""
Phase 4.0 — Intelligence Persistent Store
Thread-safe, atomic persistent store for intelligence tasks, contracts, and extracted evidence items.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from intelligence.schemas import IntelligenceResult, EvidenceItem, TaskStatus
from intelligence.errors import IntelligenceError, TASK_NOT_FOUND
from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTELLIGENCE_STORE_FILE = os.path.join(BASE_DIR, "intelligence_store.json")

_store_lock = threading.RLock()
MAX_TASKS_PER_TENANT = 500


class IntelligenceStore:
    """Thread-safe store for tasks, evidence records, and traces."""

    def __init__(self, file_path: Optional[str] = None):
        self.path = file_path or INTELLIGENCE_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self) -> None:
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"tasks": {}, "evidence": {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[intelligence_store] Failed to create {self.path}: {e}")

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
            self._cache = {"tasks": {}, "evidence": {}}
            self._cache_mtime = 0
            return self._cache

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
            if not isinstance(self._cache, dict):
                self._cache = {"tasks": {}, "evidence": {}}
            if "tasks" not in self._cache:
                self._cache["tasks"] = {}
            if "evidence" not in self._cache:
                self._cache["evidence"] = {}
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except json.JSONDecodeError as jde:
            logger.error(f"[intelligence_store] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now(timezone.utc).timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
            except Exception:
                pass
            self._cache = {"tasks": {}, "evidence": {}}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"[intelligence_store] Failed to load {self.path}: {e}")
            self._cache = {"tasks": {}, "evidence": {}}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict) -> None:
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path) or "."
        temp_fd, temp_path = tempfile.mkstemp(
            prefix="intelligence_store_", suffix=".tmp", dir=dir_name
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, self.path)
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0
        except Exception as e:
            logger.error(f"[intelligence_store] Failed to save {self.path}: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def save_task(self, task: IntelligenceResult) -> None:
        with _store_lock:
            data = self._load_under_lock()
            t_dict = task.model_dump()
            data["tasks"][task.task_id] = t_dict

            # Prune old completed tasks if exceeding MAX_TASKS_PER_TENANT
            tenant_tasks = [
                (k, v) for k, v in data["tasks"].items() if v.get("tenant_id") == task.tenant_id
            ]
            if len(tenant_tasks) > MAX_TASKS_PER_TENANT:
                # Keep active/recent ones
                sorted_tasks = sorted(
                    tenant_tasks,
                    key=lambda x: x[1].get("created_at", ""),
                )
                for old_id, _ in sorted_tasks[:-MAX_TASKS_PER_TENANT]:
                    data["tasks"].pop(old_id, None)

            self._save_under_lock(data)

    def get_task(self, task_id: str, tenant_id: Optional[str] = None) -> Optional[IntelligenceResult]:
        with _store_lock:
            data = self._load_under_lock()
            raw = data["tasks"].get(task_id)
            if not raw:
                return None
            if tenant_id and raw.get("tenant_id") != tenant_id:
                return None
            return IntelligenceResult(**raw)

    def list_tasks(self, tenant_id: str, limit: int = 50) -> List[IntelligenceResult]:
        with _store_lock:
            data = self._load_under_lock()
            matched = [
                IntelligenceResult(**v)
                for v in data["tasks"].values()
                if v.get("tenant_id") == tenant_id
            ]
            matched.sort(key=lambda x: x.created_at, reverse=True)
            return matched[:limit]

    def save_evidence(self, evidence_item: EvidenceItem, tenant_id: str) -> None:
        with _store_lock:
            data = self._load_under_lock()
            ev_dict = evidence_item.model_dump()
            ev_dict["tenant_id"] = tenant_id
            data["evidence"][evidence_item.evidence_id] = ev_dict
            self._save_under_lock(data)

    def get_evidence(self, evidence_id: str, tenant_id: Optional[str] = None) -> Optional[EvidenceItem]:
        with _store_lock:
            data = self._load_under_lock()
            raw = data["evidence"].get(evidence_id)
            if not raw:
                return None
            if tenant_id and raw.get("tenant_id") != tenant_id:
                return None
            clean_raw = {k: v for k, v in raw.items() if k != "tenant_id"}
            return EvidenceItem(**clean_raw)

    def list_evidence_for_task(self, evidence_ids: List[str], tenant_id: str) -> List[EvidenceItem]:
        with _store_lock:
            data = self._load_under_lock()
            results = []
            for eid in evidence_ids:
                raw = data["evidence"].get(eid)
                if raw and raw.get("tenant_id") == tenant_id:
                    clean_raw = {k: v for k, v in raw.items() if k != "tenant_id"}
                    results.append(EvidenceItem(**clean_raw))
            return results
