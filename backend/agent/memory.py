"""
Phase 2I — Agent Memory Engine
Bounded persistent storage for agent memories, references, and user preferences.
Thread-safe, atomic, corruption-resilient, with strict 500-records-per-tenant bounds.
"""
from __future__ import annotations
import json
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_MEMORY_STORE_FILE = os.path.join(BASE_DIR, "agent_memory_store.json")

_store_lock = threading.RLock()
MAX_RECORDS_PER_TENANT = 500


class AgentMemoryStore:
    """Persistent storage for bounded contextual memories per tenant."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or AGENT_MEMORY_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0
                except Exception as e:
                    logger.error(f"[agent_memory] Failed to create {self.path}: {e}")

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
            self._cache = {}
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
            logger.error(f"[agent_memory] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[agent_memory] Saved corrupted store to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[agent_memory] Failed to backup corrupted store: {be}")
            self._cache = {}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception as we:
                logger.error(f"[agent_memory] Failed to write fresh store file: {we}")
        except Exception as e:
            logger.error(f"[agent_memory] Failed to load {self.path}: {e}")
            self._cache = {}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="agent_mem_tmp_", suffix=".json"
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
            logger.error(f"[agent_memory] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def record_memory(
        self,
        tenant_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Saves a bounded memory record for a tenant."""
        with _store_lock:
            data = self._load_under_lock()
            tenant_records = data.get(tenant_id, [])

            memory_id = f"mem_{uuid.uuid4().hex[:10]}"
            entry = {
                "memory_id": memory_id,
                "memory_type": memory_type,
                "content": str(content)[:500],
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            tenant_records.append(entry)
            # Enforce 500 records bound per tenant
            if len(tenant_records) > MAX_RECORDS_PER_TENANT:
                tenant_records = tenant_records[-MAX_RECORDS_PER_TENANT:]

            data[tenant_id] = tenant_records
            self._save_under_lock(data)
            return memory_id

    def get_tenant_memories(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with _store_lock:
            data = self._load_under_lock()
            recs = data.get(tenant_id, [])
            return recs[-limit:]
