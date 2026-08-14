"""
Phase 2C — PlannerStore
Atomic, thread-safe persistence for generated plans.
Mirrors the proven Phase 1 / Phase 2A pattern: threading.Lock + temp-file replace + corruption recovery.
"""
import json
import os
import shutil
import tempfile
import threading
from datetime import datetime, timezone
from typing import Optional


from utils.logger import logger

PLANNER_STORE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "planner_store.json"
)

_store_lock = threading.Lock()

# Maximum plans retained (oldest pruned when exceeded)
MAX_STORED_PLANS = 500


class PlannerStore:
    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or PLANNER_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0
        self._ensure_file()


    def _ensure_file(self):
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump({"plans": {}}, f)
                except Exception as e:
                    logger.error(f"[planner_store] Failed to create store file: {e}")

    def _load_under_lock(self) -> dict:
        if not os.path.exists(self.path):
            return {"plans": {}}

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as jde:
            logger.error(f"[planner_store] JSON corrupted: {jde}")
            corrupt_backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
            try:
                shutil.copy2(self.path, corrupt_backup)
                logger.warning(f"[planner_store] Saved corrupted file to {corrupt_backup}")
            except Exception as be:
                logger.error(f"[planner_store] Failed to copy corrupt file: {be}")
            fresh = {"plans": {}}
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(fresh, f)
            except Exception as we:
                logger.error(f"[planner_store] Failed to write fresh file during recovery: {we}")
            return fresh
        except Exception as e:
            logger.error(f"[planner_store] Failed to load store: {e}")
            return {"plans": {}}

    def _save_under_lock(self, data: dict):
        dir_name = os.path.dirname(self.path)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_name, prefix="planner_store_tmp_", suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
                f.flush()
            try:
                os.replace(temp_path, self.path)
            except Exception:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"[planner_store] Atomic save failed: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass



    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_plan(self, plan_id: str, plan_data: dict):
        """Persist a plan under plan_id, pruning oldest if limit exceeded."""
        with _store_lock:
            data = self._load_under_lock()
            plans = data.get("plans", {})
            import time
            plan_data["_saved_at"] = time.time()
            if "created_at" not in plan_data:
                plan_data["created_at"] = datetime.now(timezone.utc).isoformat()
            plans[plan_id] = plan_data
            # Prune oldest entries if over limit
            if len(plans) > MAX_STORED_PLANS:
                # Sort by _saved_at ascending; drop oldest
                sorted_keys = sorted(
                    plans.keys(),
                    key=lambda k: plans[k].get("_saved_at", 0),
                )
                for old_key in sorted_keys[: len(plans) - MAX_STORED_PLANS]:
                    del plans[old_key]
            data["plans"] = plans
            self._save_under_lock(data)



    def get_plan(self, plan_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("plans", {}).get(plan_id)

    def list_plans_for_workspace(self, workspace_id: str) -> list:
        with _store_lock:
            data = self._load_under_lock()
            return [
                v for v in data.get("plans", {}).values()
                if v.get("workspace_id") == workspace_id
            ]
