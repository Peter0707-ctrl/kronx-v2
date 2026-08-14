"""
Phase 2H — Tenant Quotas Engine
Tracks and enforces server-side resource usage quotas per tenant.
"""
from __future__ import annotations
import threading
from typing import Dict
from config.settings import config
from gateway.errors import GatewayError, QUOTA_EXCEEDED
from gateway.schemas import QuotaUsage

_quota_lock = threading.RLock()


class TenantQuotaManager:
    """Manages resource quotas per tenant."""

    def __init__(self):
        self._active_jobs: Dict[str, int] = {}
        self._workspaces_count: Dict[str, int] = {}
        self._sessions_count: Dict[str, int] = {}

    def check_workspace_quota(self, tenant_id: str, current_count: int):
        if current_count >= config.max_tenant_workspaces:
            raise GatewayError(
                code=QUOTA_EXCEEDED,
                detail=f"Tenant workspace quota reached (maximum {config.max_tenant_workspaces}).",
                status_code=429,
            )

    def check_session_quota(self, tenant_id: str, current_count: int):
        if current_count >= config.max_tenant_sessions:
            raise GatewayError(
                code=QUOTA_EXCEEDED,
                detail=f"Tenant active session quota reached (maximum {config.max_tenant_sessions}).",
                status_code=429,
            )

    def acquire_job_slot(self, tenant_id: str):
        with _quota_lock:
            current = self._active_jobs.get(tenant_id, 0)
            if current >= config.max_tenant_concurrent_jobs:
                raise GatewayError(
                    code=QUOTA_EXCEEDED,
                    detail=f"Tenant concurrent job quota exceeded (maximum {config.max_tenant_concurrent_jobs}).",
                    status_code=429,
                )
            self._active_jobs[tenant_id] = current + 1

    def release_job_slot(self, tenant_id: str):
        with _quota_lock:
            current = self._active_jobs.get(tenant_id, 0)
            if current > 0:
                self._active_jobs[tenant_id] = current - 1
            if self._active_jobs.get(tenant_id) == 0:
                self._active_jobs.pop(tenant_id, None)

    def get_quota_usage(self, tenant_id: str) -> QuotaUsage:
        with _quota_lock:
            return QuotaUsage(
                tenant_id=tenant_id,
                active_sessions=self._sessions_count.get(tenant_id, 0),
                registered_workspaces=self._workspaces_count.get(tenant_id, 0),
                concurrent_jobs=self._active_jobs.get(tenant_id, 0),
            )


quota_manager = TenantQuotaManager()
