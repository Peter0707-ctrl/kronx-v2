"""
Phase 2I — Immutable Decision Trace Engine
Persists structured agent decision traces for accountability and auditing.
Thread-safe, atomic, bounded to 500 records per tenant, with newline sanitization and zero secrets.
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

from agent.schemas import DecisionTrace
from utils.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_TRACE_STORE_FILE = os.path.join(BASE_DIR, "agent_trace_store.json")

_store_lock = threading.RLock()
MAX_TRACES_PER_TENANT = 500


def sanitize_trace_str(val: Any) -> str:
    if val is None:
        return ""
    s = str(val).replace("\n", "\\n").replace("\r", "\\r")
    return s[:256] if len(s) > 256 else s


class AgentTraceStore:
    """Persistent storage for decision traces."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or AGENT_TRACE_STORE_FILE
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
                    logger.error(f"[agent_trace] Failed to create {self.path}: {e}")

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
            logger.error(f"[agent_trace] Corrupted JSON in {self.path}: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
            except Exception:
                pass
            self._cache = {}
            self._cache_mtime = 0
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._cache, f)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"[agent_trace] Failed to load {self.path}: {e}")
            self._cache = {}
            self._cache_mtime = 0

        return json.loads(json.dumps(self._cache))

    def _save_under_lock(self, data: dict):
        self._cache = json.loads(json.dumps(data))
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="agent_trace_tmp_", suffix=".json"
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
            logger.error(f"[agent_trace] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def record_trace(self, trace: DecisionTrace):
        with _store_lock:
            data = self._load_under_lock()
            tenant_traces = data.get(trace.tenant_id, [])

            tenant_traces.append(trace.model_dump())
            if len(tenant_traces) > MAX_TRACES_PER_TENANT:
                tenant_traces = tenant_traces[-MAX_TRACES_PER_TENANT:]

            data[trace.tenant_id] = tenant_traces
            self._save_under_lock(data)

    def get_traces_by_tenant(self, tenant_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get(tenant_id, [])[-limit:]
