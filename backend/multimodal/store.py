"""
Phase 2I.1 — Multimodal Result Store
Thread-safe, atomic, multi-tenant persistent store for multimodal intelligence records.
"""
import os
import json
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from multimodal.schemas import MultimodalResult, MultimodalStatus
from multimodal.limits import MAX_STORED_RECORDS_PER_TENANT
from multimodal.errors import MultimodalError, STORE_ERROR, RESOURCE_NOT_FOUND
from utils.logger import logger

MULTIMODAL_STORE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "multimodal_store.json"
)

_store_lock = threading.RLock()


class MultimodalStore:
    """Multi-tenant atomic persistent store for multimodal execution results."""

    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or MULTIMODAL_STORE_FILE
        self._ensure_file()

    def _ensure_file(self) -> None:
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    os.makedirs(os.path.dirname(self.path), exist_ok=True)
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"tenants": {}}, f)
                except Exception as e:
                    logger.error(f"[multimodal_store] Failed to create store file: {e}")

    def _load_under_lock(self) -> dict:
        if not os.path.exists(self.path):
            return {"tenants": {}}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as jde:
            logger.error(f"[multimodal_store] JSON corrupted: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[multimodal_store] Saved corrupted store to {corrupt_backup}")
            except Exception:
                pass
            fresh = {"tenants": {}}
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(fresh, f)
            except Exception:
                pass
            return fresh
        except Exception as e:
            logger.error(f"[multimodal_store] Failed to load store: {e}")
            return {"tenants": {}}

    def _save_under_lock(self, data: dict) -> None:
        dir_name = os.path.dirname(self.path)
        os.makedirs(dir_name, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="mm_store_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
            try:
                os.replace(temp_path, self.path)
            except Exception:
                # Windows fallback
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[multimodal_store] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Public API (Strict Tenant Isolation)
    # ------------------------------------------------------------------

    def save_result(self, result: MultimodalResult) -> None:
        """Saves or updates a multimodal result strictly scoped under tenant_id."""
        with _store_lock:
            data = self._load_under_lock()
            tenants = data.setdefault("tenants", {})
            tenant_records = tenants.setdefault(result.tenant_id, {})

            tenant_records[result.request_id] = result.model_dump()

            # Bound tenant records to MAX_STORED_RECORDS_PER_TENANT
            if len(tenant_records) > MAX_STORED_RECORDS_PER_TENANT:
                sorted_keys = sorted(
                    tenant_records.keys(),
                    key=lambda k: tenant_records[k].get("created_at", ""),
                )
                for old_key in sorted_keys[: len(tenant_records) - MAX_STORED_RECORDS_PER_TENANT]:
                    del tenant_records[old_key]

            self._save_under_lock(data)

    def get_result(self, request_id: str, tenant_id: str) -> Optional[MultimodalResult]:
        """Retrieves a result if owned by the requesting tenant."""
        with _store_lock:
            data = self._load_under_lock()
            tenants = data.get("tenants", {})
            tenant_records = tenants.get(tenant_id, {})
            record_dict = tenant_records.get(request_id)
            if record_dict:
                return MultimodalResult.model_validate(record_dict)
            return None

    def list_results(self, tenant_id: str, limit: int = 50) -> List[MultimodalResult]:
        """Lists recent results for the tenant."""
        with _store_lock:
            data = self._load_under_lock()
            tenants = data.get("tenants", {})
            tenant_records = tenants.get(tenant_id, {})
            results = [MultimodalResult.model_validate(r) for r in tenant_records.values()]
            results.sort(key=lambda r: r.created_at, reverse=True)
            return results[:limit]

    def update_status(self, request_id: str, tenant_id: str, status: MultimodalStatus) -> bool:
        """Updates status of a request in-place under tenant lock."""
        with _store_lock:
            data = self._load_under_lock()
            tenants = data.get("tenants", {})
            tenant_records = tenants.get(tenant_id, {})
            if request_id in tenant_records:
                tenant_records[request_id]["status"] = status.value
                self._save_under_lock(data)
                return True
            return False
