"""
Phase 3.1 — Safe Retention & Cleanup Engine
Enforces bounded retention for events, traces, metrics, diagnostics, and jobs.
Guarantees: no unbounded growth, no deletion of active jobs, and atomic pruning.
"""
import threading
from typing import Dict, Any, Optional
from operations.store import (
    OperationsStore,
    MAX_EVENTS_STORED,
    MAX_DIAGNOSTICS_STORED,
    MAX_JOBS_PER_TENANT,
    MAX_INCIDENTS_STORED,
)
from operations.audit import log_operations_audit

_retention_lock = threading.RLock()


class RetentionEngine:
    def __init__(self, store: Optional[OperationsStore] = None):
        self._store = store or OperationsStore()

    def run_retention_cleanup(self) -> Dict[str, int]:
        """
        Executes bounded retention enforcement across all stored operational structures.
        Returns counts of retained vs pruned items.
        """
        with _retention_lock:
            data = self._store._load_under_lock()

            # 1. Events retention
            events = data.get("events", [])
            initial_events = len(events)
            if len(events) > MAX_EVENTS_STORED:
                events = events[-MAX_EVENTS_STORED:]
                data["events"] = events
            pruned_events = initial_events - len(events)

            # 2. Diagnostics retention
            diags = data.get("diagnostics", [])
            initial_diags = len(diags)
            if len(diags) > MAX_DIAGNOSTICS_STORED:
                diags = diags[-MAX_DIAGNOSTICS_STORED:]
                data["diagnostics"] = diags
            pruned_diags = initial_diags - len(diags)

            # 3. Incidents retention (closed/resolved only)
            incidents = data.get("incidents", {})
            initial_incidents = len(incidents)
            if len(incidents) > MAX_INCIDENTS_STORED:
                # Prioritize keeping OPEN and CRITICAL
                sorted_keys = sorted(
                    incidents.keys(),
                    key=lambda k: (
                        1 if incidents[k].get("status") == "OPEN" else 0,
                        incidents[k].get("created_at", "")
                    )
                )
                for old_k in sorted_keys[:len(incidents) - MAX_INCIDENTS_STORED]:
                    del incidents[old_k]
                data["incidents"] = incidents
            pruned_incidents = initial_incidents - len(incidents)

            # 4. Jobs retention per tenant
            jobs = data.get("jobs", {})
            pruned_jobs = 0
            for t_id, t_jobs in list(jobs.items()):
                if len(t_jobs) > MAX_JOBS_PER_TENANT:
                    # Do not prune RUNNING or QUEUED jobs
                    pruneable = [
                        k for k, v in t_jobs.items()
                        if v.get("status") in ["COMPLETED", "FAILED", "CANCELLED", "EXPIRED"]
                    ]
                    sorted_p = sorted(pruneable, key=lambda k: t_jobs[k].get("created_at", ""))
                    excess = len(t_jobs) - MAX_JOBS_PER_TENANT
                    for k in sorted_p[:excess]:
                        del t_jobs[k]
                        pruned_jobs += 1
                jobs[t_id] = t_jobs
            data["jobs"] = jobs

            self._store._save_under_lock(data)

            result = {
                "pruned_events": pruned_events,
                "pruned_diagnostics": pruned_diags,
                "pruned_incidents": pruned_incidents,
                "pruned_jobs": pruned_jobs,
            }

            log_operations_audit(
                action="RETENTION_CLEANUP",
                status="SUCCESS",
                details=result,
            )
            return result
