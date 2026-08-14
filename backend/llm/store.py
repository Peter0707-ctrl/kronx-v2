"""
Phase 2J — LLM Persistent Store
Thread-safe atomic persistence for inference records with multi-tenant partitioning and corruption recovery.
"""
from __future__ import annotations
import os
import json
import time
import shutil
import tempfile
import threading
from typing import Dict, List, Optional, Any

from utils.logger import logger
from llm.schemas import LLMInferenceRecord

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LLM_STORE = os.path.join(BASE_DIR, "llm_store.json")

_store_lock = threading.RLock()
MAX_STORED_RECORDS_PER_TENANT = 500


class LLMStore:
    """Atomic JSON persistent store for multi-tenant inference history."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or DEFAULT_LLM_STORE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0.0
        self._ensure_file()

    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"records": {}}, f)
                    try:
                        self._cache_mtime = os.path.getmtime(self.path)
                    except Exception:
                        self._cache_mtime = 0.0
                except Exception as e:
                    logger.error(f"[llm_store] Failed to initialize {self.path}: {e}")

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
            self._cache = {"records": {}}
            return {"records": {}}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict) or "records" not in data:
                    raise ValueError("Malformed llm_store schema")
                self._cache = data
                try:
                    self._cache_mtime = os.path.getmtime(self.path)
                except Exception:
                    pass
                return json.loads(json.dumps(self._cache))
        except Exception as e:
            logger.error(f"[llm_store] JSON corrupted: {e}")
            backup = f"{self.path}.corrupt.{int(time.time())}"
            try:
                shutil.copyfile(self.path, backup)
                logger.warning(f"[llm_store] Saved corrupted store to {backup}")
            except Exception:
                pass
            recovered = {"records": {}}
            self._cache = recovered
            self._save_under_lock(recovered)
            return recovered

    def _save_under_lock(self, data: dict):
        dname = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(dname, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=dname, prefix="llm_tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)
            self._cache = data
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                pass
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            logger.error(f"[llm_store] Failed atomic save to {self.path}: {e}")
            raise

    def save_record(self, record: LLMInferenceRecord):
        with _store_lock:
            data = self._load_under_lock()
            recs = data.setdefault("records", {})
            tenant_recs = recs.setdefault(record.tenant_id, {})
            tenant_recs[record.request_id] = record.model_dump()

            if len(tenant_recs) > MAX_STORED_RECORDS_PER_TENANT:
                sorted_keys = sorted(
                    tenant_recs.keys(),
                    key=lambda k: tenant_recs[k].get("created_at", ""),
                )
                for old_k in sorted_keys[: len(tenant_recs) - MAX_STORED_RECORDS_PER_TENANT]:
                    del tenant_recs[old_k]

            self._save_under_lock(data)

    def get_record(self, request_id: str, tenant_id: str) -> Optional[LLMInferenceRecord]:
        with _store_lock:
            data = self._load_under_lock()
            tenant_recs = data.get("records", {}).get(tenant_id, {})
            raw = tenant_recs.get(request_id)
            if raw:
                return LLMInferenceRecord.model_validate(raw)
            return None

    def list_records(self, tenant_id: str, limit: int = 50) -> List[LLMInferenceRecord]:
        with _store_lock:
            data = self._load_under_lock()
            tenant_recs = data.get("records", {}).get(tenant_id, {})
            results = [LLMInferenceRecord.model_validate(r) for r in tenant_recs.values()]
            results.sort(key=lambda r: r.created_at, reverse=True)
            return results[:limit]
