"""
Phase 3.1 — OperationsStore
Thread-safe, atomic JSON persistence for lifecycle state, jobs, events, incidents, backups, and metrics.
"""
import os
import json
import shutil
import tempfile
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from utils.logger import logger

OPERATIONS_STORE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "operations_store.json"
)

_store_lock = threading.RLock()
MAX_EVENTS_STORED = 1000
MAX_DIAGNOSTICS_STORED = 200
MAX_JOBS_PER_TENANT = 200
MAX_INCIDENTS_STORED = 500


class OperationsStore:
    def __init__(self, store_path: Optional[str] = None):
        self.path = store_path or OPERATIONS_STORE_FILE
        self._cache: Optional[dict] = None
        self._cache_mtime: float = 0.0
        self._ensure_file()

    def _ensure_file(self) -> None:
        with _store_lock:
            if not os.path.exists(self.path):
                try:
                    init_data = {
                        "lifecycle": {
                            "state": "READY",
                            "active_jobs": 0,
                            "draining": False,
                            "started_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "details": "System operating normally."
                        },
                        "events": [],
                        "jobs": {},
                        "incidents": {},
                        "backups": [],
                        "diagnostics": [],
                        "metrics": {}
                    }
                    with open(self.path, "w", encoding="utf-8") as f:
                        json.dump(init_data, f, indent=2)
                except Exception as e:
                    logger.error(f"[operations_store] Failed to initialize {self.path}: {e}")

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
            self._cache = {
                "lifecycle": {"state": "READY", "active_jobs": 0, "draining": False},
                "events": [], "jobs": {}, "incidents": {}, "backups": [], "diagnostics": [], "metrics": {}
            }
            self._cache_mtime = 0.0
            return self._cache

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            # Normalize list/dict schemas
            if isinstance(loaded.get("diagnostics"), dict):
                loaded["diagnostics"] = list(loaded["diagnostics"].values())
            if isinstance(loaded.get("backups"), dict):
                loaded["backups"] = list(loaded["backups"].values())
            if not isinstance(loaded.get("events"), list):
                loaded["events"] = []
            if not isinstance(loaded.get("jobs"), dict):
                loaded["jobs"] = {}
            if not isinstance(loaded.get("incidents"), dict):
                loaded["incidents"] = {}

            self._cache = loaded
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0.0
            return json.loads(json.dumps(self._cache))
        except Exception as e:
            logger.error(f"[operations_store] Corrupt store detected: {e}")
            try:
                backup = f"{self.path}.corrupt.{int(datetime.now().timestamp())}"
                shutil.copy2(self.path, backup)
                logger.warning(f"[operations_store] Saved corrupt store to {backup}")
            except Exception:
                pass
            fresh = {
                "lifecycle": {"state": "READY", "active_jobs": 0, "draining": False},
                "events": [], "jobs": {}, "incidents": {}, "backups": [], "diagnostics": [], "metrics": {}
            }
            self._save_under_lock(fresh)
            return fresh


    def _save_under_lock(self, data: dict) -> None:
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=parent, prefix="ops_tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            shutil.move(temp_path, self.path)
            self._cache = json.loads(json.dumps(data))
            try:
                self._cache_mtime = os.path.getmtime(self.path)
            except Exception:
                self._cache_mtime = 0.0
        except Exception as e:
            logger.error(f"[operations_store] Save error: {e}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            raise e

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def get_lifecycle(self) -> dict:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("lifecycle", {"state": "READY", "active_jobs": 0, "draining": False})

    def save_lifecycle(self, lifecycle_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            data["lifecycle"] = lifecycle_dict
            self._save_under_lock(data)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def record_event(self, event_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            events = data.get("events", [])
            events.append(event_dict)
            if len(events) > MAX_EVENTS_STORED:
                events = events[-MAX_EVENTS_STORED:]
            data["events"] = events
            self._save_under_lock(data)

    def get_events(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        with _store_lock:
            data = self._load_under_lock()
            events = data.get("events", [])
            if tenant_id:
                events = [e for e in events if e.get("tenant_id") == tenant_id]
            return events[-limit:][::-1]

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------
    def save_job(self, tenant_id: str, job_id: str, job_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            jobs = data.get("jobs", {})
            t_jobs = jobs.get(tenant_id, {})
            t_jobs[job_id] = job_dict
            if len(t_jobs) > MAX_JOBS_PER_TENANT:
                # prune oldest
                sorted_keys = sorted(t_jobs.keys(), key=lambda k: t_jobs[k].get("created_at", ""))
                for old_k in sorted_keys[:len(t_jobs) - MAX_JOBS_PER_TENANT]:
                    del t_jobs[old_k]
            jobs[tenant_id] = t_jobs
            data["jobs"] = jobs
            self._save_under_lock(data)

    def get_job(self, tenant_id: str, job_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("jobs", {}).get(tenant_id, {}).get(job_id)

    def list_jobs(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        with _store_lock:
            data = self._load_under_lock()
            jobs = data.get("jobs", {})
            if tenant_id:
                t_jobs = list(jobs.get(tenant_id, {}).values())
                return sorted(t_jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:limit]
            all_jobs = []
            for t_dict in jobs.values():
                all_jobs.extend(t_dict.values())
            return sorted(all_jobs, key=lambda j: j.get("created_at", ""), reverse=True)[:limit]

    # ------------------------------------------------------------------
    # Incidents
    # ------------------------------------------------------------------
    def save_incident(self, incident_id: str, inc_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            incidents = data.get("incidents", {})
            incidents[incident_id] = inc_dict
            if len(incidents) > MAX_INCIDENTS_STORED:
                sorted_keys = sorted(incidents.keys(), key=lambda k: incidents[k].get("created_at", ""))
                for old_k in sorted_keys[:len(incidents) - MAX_INCIDENTS_STORED]:
                    del incidents[old_k]
            data["incidents"] = incidents
            self._save_under_lock(data)

    def get_incident(self, incident_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            return data.get("incidents", {}).get(incident_id)

    def list_incidents(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[dict]:
        with _store_lock:
            data = self._load_under_lock()
            incidents = list(data.get("incidents", {}).values())
            if tenant_id:
                incidents = [i for i in incidents if i.get("tenant_id") == tenant_id]
            return sorted(incidents, key=lambda i: i.get("created_at", ""), reverse=True)[:limit]

    # ------------------------------------------------------------------
    # Backups
    # ------------------------------------------------------------------
    def record_backup(self, backup_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            backups = data.get("backups", [])
            backups.append(backup_dict)
            data["backups"] = backups
            self._save_under_lock(data)

    def list_backups(self, store_name: Optional[str] = None) -> List[dict]:
        with _store_lock:
            data = self._load_under_lock()
            backups = data.get("backups", [])
            if store_name:
                backups = [b for b in backups if b.get("store_name") == store_name]
            return sorted(backups, key=lambda b: b.get("timestamp", ""), reverse=True)

    def get_backup(self, backup_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            for b in data.get("backups", []):
                if b.get("backup_id") == backup_id:
                    return b
            return None

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def record_diagnostic(self, diag_dict: dict) -> None:
        with _store_lock:
            data = self._load_under_lock()
            diags = data.get("diagnostics", [])
            diags.append(diag_dict)
            if len(diags) > MAX_DIAGNOSTICS_STORED:
                diags = diags[-MAX_DIAGNOSTICS_STORED:]
            data["diagnostics"] = diags
            self._save_under_lock(data)

    def get_diagnostic(self, diag_id: str) -> Optional[dict]:
        with _store_lock:
            data = self._load_under_lock()
            for d in data.get("diagnostics", []):
                if d.get("diagnostic_id") == diag_id:
                    return d
            return None
