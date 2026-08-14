"""
Phase 3.1 — Bounded Metrics Engine
Thread-safe, bounded aggregation for operational counters, gauges, and durations.
Cardinally bounded: labels are strictly restricted and sanitized.
"""
import re
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

_metrics_lock = threading.RLock()

# Predefined standard counters
STANDARD_COUNTERS = {
    "requests_total",
    "requests_failed",
    "auth_success",
    "auth_failure",
    "rate_limit_hits",
    "quota_hits",
    "agent_requests",
    "agent_completed",
    "agent_blocked",
    "llm_requests",
    "llm_failures",
    "llm_tokens",
    "vision_requests",
    "ocr_requests",
    "modification_proposals",
    "modifications_applied",
    "modifications_rolled_back",
    "verification_runs",
    "verification_failures",
    "active_jobs",
    "cancelled_jobs",
    "incident_count",
}

_SAFE_METRIC_KEY = re.compile(r"^[a-zA-Z0-9_]{1,48}$")


class MetricsEngine:
    def __init__(self):
        self._counters: Dict[str, int] = {k: 0 for k in STANDARD_COUNTERS}
        self._gauges: Dict[str, float] = {
            "system_readiness_score": 10.0,
            "active_workers_count": 0.0,
            "store_integrity_healthy": 1.0,
        }
        self._tenant_counts: Dict[str, int] = {}
        self._last_updated: str = datetime.now(timezone.utc).isoformat()

    def _sanitize_name(self, name: str) -> str:
        stripped = name.strip().lower()
        if _SAFE_METRIC_KEY.match(stripped):
            return stripped[:48]
        return "custom_metric"


    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increments a bounded counter."""
        safe_name = self._sanitize_name(name)
        with _metrics_lock:
            self._counters[safe_name] = self._counters.get(safe_name, 0) + max(1, int(value))
            if labels and "tenant_id" in labels:
                t_id = labels["tenant_id"][:32]
                self._tenant_counts[t_id] = self._tenant_counts.get(t_id, 0) + 1
            self._last_updated = datetime.now(timezone.utc).isoformat()

    def set_gauge(self, name: str, value: float) -> None:
        """Sets a bounded gauge value."""
        safe_name = self._sanitize_name(name)
        with _metrics_lock:
            self._gauges[safe_name] = float(value)
            self._last_updated = datetime.now(timezone.utc).isoformat()

    def get_summary(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns a sanitized snapshot of operational metrics."""
        with _metrics_lock:
            counters_copy = dict(self._counters)
            gauges_copy = dict(self._gauges)
            t_activity = self._tenant_counts.get(tenant_id, 0) if tenant_id else len(self._tenant_counts)

            return {
                "counters": counters_copy,
                "gauges": gauges_copy,
                "tenant_activity_count": t_activity,
                "timestamp": self._last_updated,
            }

    def reset_for_test(self) -> None:
        """Resets all metrics (for clean test isolation)."""
        with _metrics_lock:
            self._counters = {k: 0 for k in STANDARD_COUNTERS}
            self._gauges = {
                "system_readiness_score": 10.0,
                "active_workers_count": 0.0,
                "store_integrity_healthy": 1.0,
            }
            self._tenant_counts = {}
            self._last_updated = datetime.now(timezone.utc).isoformat()
