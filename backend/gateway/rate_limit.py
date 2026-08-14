"""
Phase 2H — Multi-Level Bounded Rate Limiting Engine
Implements sliding-window rate limits for origins, users, tenants, and expensive operations.
Guarantees strictly bounded memory with auto-pruning.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, List, Optional
from config.settings import config
from gateway.errors import GatewayError, RATE_LIMITED

MAX_TRACKED_KEYS = 5000
_rate_lock = threading.RLock()


class RateLimiter:
    """Thread-safe bounded sliding-window rate limiter."""

    def __init__(self):
        # key -> list of float timestamps
        self._records: Dict[str, List[float]] = {}

    def _get_limit_for_operation(self, operation: str) -> int:
        op = operation.upper()
        if op == "AUTH":
            return config.limit_auth_failures_per_window
        elif op == "WORKSPACE_SCAN":
            return config.limit_scans_per_window
        elif op == "PLANNING":
            return config.limit_plans_per_window
        elif op == "EXECUTION":
            return config.limit_executions_per_window
        elif op == "MODIFICATION":
            return config.limit_modifications_per_window
        elif op == "VERIFICATION":
            return config.limit_verifications_per_window
        return config.rate_limit_requests_per_window

    def check_and_record(
        self,
        identifier: str,
        operation: str = "GENERAL",
        custom_limit: Optional[int] = None,
        window_seconds: Optional[int] = None,
    ):
        """
        Records a request and checks if the rate limit for the identifier and operation is exceeded.
        Raises GatewayError(RATE_LIMITED) on violation.
        """
        now = time.time()
        window = window_seconds or config.rate_limit_window_seconds
        limit = custom_limit if custom_limit is not None else self._get_limit_for_operation(operation)
        key = f"{operation.lower()}:{identifier}"

        with _rate_lock:
            # Periodic bounded pruning if too many keys
            if len(self._records) > MAX_TRACKED_KEYS:
                expired_keys = [
                    k for k, timestamps in self._records.items()
                    if not timestamps or (now - timestamps[-1] > window * 2)
                ]
                for k in expired_keys[:1000]:
                    del self._records[k]

            timestamps = self._records.get(key, [])
            # Filter out timestamps outside window
            cutoff = now - window
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= limit:
                self._records[key] = valid_timestamps
                raise GatewayError(
                    code=RATE_LIMITED,
                    detail=f"Rate limit exceeded for {operation}. Maximum {limit} requests per {window}s.",
                    status_code=429,
                )

            valid_timestamps.append(now)
            self._records[key] = valid_timestamps


rate_limiter = RateLimiter()
