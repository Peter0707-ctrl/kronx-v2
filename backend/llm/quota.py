"""
Phase 2J — LLM Tenant & User Request Quota Engine
Bounded sliding-window rate limiting for inference requests.
"""
import time
import threading
from typing import Dict, Optional
from llm.schemas import LLMQuota
from llm.errors import LLMError, QUOTA_EXCEEDED

_quota_lock = threading.RLock()

DEFAULT_MAX_RPM = 60
DEFAULT_MAX_RPH = 1000


class LLMQuotaManager:
    """Tracks and enforces inference request rate quotas per tenant."""

    def __init__(self):
        self._quotas: Dict[str, LLMQuota] = {}

    def get_or_create_quota(self, tenant_id: str) -> LLMQuota:
        with _quota_lock:
            now = time.time()
            if tenant_id not in self._quotas:
                self._quotas[tenant_id] = LLMQuota(
                    tenant_id=tenant_id,
                    max_requests_per_minute=DEFAULT_MAX_RPM,
                    max_requests_per_hour=DEFAULT_MAX_RPH,
                    last_reset_minute=now,
                    last_reset_hour=now,
                )
            return self._quotas[tenant_id]

    def set_quota_limits(
        self,
        tenant_id: str,
        max_rpm: Optional[int] = None,
        max_rph: Optional[int] = None,
    ):
        with _quota_lock:
            quota = self.get_or_create_quota(tenant_id)
            if max_rpm is not None:
                quota.max_requests_per_minute = max_rpm
            if max_rph is not None:
                quota.max_requests_per_hour = max_rph

    def check_and_increment(self, tenant_id: str):
        """Verifies quota limits and increments counter if allowed."""
        with _quota_lock:
            now = time.time()
            quota = self.get_or_create_quota(tenant_id)

            # Reset minute bucket if > 60s
            if now - quota.last_reset_minute >= 60.0:
                quota.current_minute_count = 0
                quota.last_reset_minute = now

            # Reset hour bucket if > 3600s
            if now - quota.last_reset_hour >= 3600.0:
                quota.current_hour_count = 0
                quota.last_reset_hour = now

            if quota.current_minute_count >= quota.max_requests_per_minute:
                raise LLMError(
                    QUOTA_EXCEEDED,
                    f"Tenant '{tenant_id}' exceeded requests per minute quota ({quota.max_requests_per_minute} RPM).",
                    details={"limit": quota.max_requests_per_minute, "current": quota.current_minute_count},
                )

            if quota.current_hour_count >= quota.max_requests_per_hour:
                raise LLMError(
                    QUOTA_EXCEEDED,
                    f"Tenant '{tenant_id}' exceeded requests per hour quota ({quota.max_requests_per_hour} RPH).",
                    details={"limit": quota.max_requests_per_hour, "current": quota.current_hour_count},
                )

            quota.current_minute_count += 1
            quota.current_hour_count += 1
