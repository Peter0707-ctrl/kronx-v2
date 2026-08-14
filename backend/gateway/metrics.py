"""
Phase 2H — Operational Metrics Engine
Maintains thread-safe bounded operational metrics with fixed label cardinality to prevent cardinality attacks.
"""
from __future__ import annotations
import threading
from typing import Dict
from gateway.schemas import MetricSnapshot

# Allowed fixed endpoint buckets to prevent cardinality explosions
ALLOWED_ENDPOINT_BUCKETS = {
    "/api/chat",
    "/api/memories",
    "/api/workspace",
    "/api/tools",
    "/api/planner",
    "/api/execution",
    "/api/modification",
    "/api/verification",
    "/api/auth",
    "/api/health",
    "OTHER",
}

_metrics_lock = threading.RLock()


class MetricsCollector:
    """Collects and aggregates gateway operational metrics."""

    def __init__(self):
        self._requests_total = 0
        self._errors_total = 0
        self._auth_failures_total = 0
        self._authz_failures_total = 0
        self._rate_limited_total = 0
        self._quota_exceeded_total = 0
        self._concurrency_rejections = 0
        self._total_latency_ms = 0.0
        self._endpoint_counts: Dict[str, int] = {bucket: 0 for bucket in ALLOWED_ENDPOINT_BUCKETS}

    def _normalize_endpoint(self, path: str) -> str:
        for bucket in ALLOWED_ENDPOINT_BUCKETS:
            if bucket != "OTHER" and path.startswith(bucket):
                return bucket
        return "OTHER"

    def record_request(self, path: str, duration_ms: float, status_code: int):
        with _metrics_lock:
            self._requests_total += 1
            self._total_latency_ms += duration_ms
            bucket = self._normalize_endpoint(path)
            self._endpoint_counts[bucket] = self._endpoint_counts.get(bucket, 0) + 1

            if status_code >= 400:
                self._errors_total += 1
            if status_code == 401:
                self._auth_failures_total += 1
            elif status_code == 403:
                self._authz_failures_total += 1
            elif status_code == 429:
                self._rate_limited_total += 1

    def record_quota_exceeded(self):
        with _metrics_lock:
            self._quota_exceeded_total += 1

    def record_concurrency_rejection(self):
        with _metrics_lock:
            self._concurrency_rejections += 1

    def get_snapshot(self) -> MetricSnapshot:
        with _metrics_lock:
            avg_lat = (self._total_latency_ms / self._requests_total) if self._requests_total > 0 else 0.0
            return MetricSnapshot(
                requests_total=self._requests_total,
                errors_total=self._errors_total,
                auth_failures_total=self._auth_failures_total,
                authz_failures_total=self._authz_failures_total,
                rate_limited_total=self._rate_limited_total,
                quota_exceeded_total=self._quota_exceeded_total,
                concurrency_rejections=self._concurrency_rejections,
                avg_latency_ms=round(avg_lat, 2),
                endpoint_counts=dict(self._endpoint_counts),
            )


metrics_collector = MetricsCollector()
