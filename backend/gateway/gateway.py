"""
Phase 2H — Central Gateway Facade
Provides a single interface to rate limiting, quotas, concurrency, abuse detection, and metrics.
"""
from __future__ import annotations
from gateway.rate_limit import rate_limiter, RateLimiter
from gateway.quotas import quota_manager, TenantQuotaManager
from gateway.concurrency import concurrency_coordinator, ConcurrencyCoordinator
from gateway.abuse import abuse_detector, AbuseDetector
from gateway.metrics import metrics_collector, MetricsCollector
from gateway.request_limits import validate_payload_size, validate_json_structure
from gateway.headers import sanitize_or_generate_request_id, get_security_headers
from gateway.errors import GatewayError


class Gateway:
    """Consolidated API Gateway coordinator."""

    def __init__(self):
        self.rate_limiter = rate_limiter
        self.quota_manager = quota_manager
        self.concurrency = concurrency_coordinator
        self.abuse_detector = abuse_detector
        self.metrics = metrics_collector


gateway = Gateway()
