"""
Phase 3.1 — Operations Orchestrator
Central coordinator unifying lifecycle, health, readiness, metrics, events, jobs, incidents, backup, recovery, and diagnostics.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from operations.schemas import (
    DashboardData,
    LifecycleStatus,
    HealthCheckResult,
    ReadinessEvaluation,
    BackupRecord,
    OperationalEvent,
)
from operations.store import OperationsStore
from operations.lifecycle import SystemLifecycleManager
from operations.health import OperationsHealthEngine
from operations.readiness import OperationsReadinessEngine
from operations.metrics import MetricsEngine
from operations.events import OperationalEventManager
from operations.jobs import JobLifecycleManager
from operations.incidents import IncidentEngine
from operations.backup import BackupEngine
from operations.recovery import RecoveryEngine
from operations.diagnostics import DiagnosticEngine
from operations.retention import RetentionEngine
from operations.configuration import ConfigurationValidator
from operations.integrity import StoreIntegrityManager


class OperationsOrchestrator:
    def __init__(self, store: Optional[OperationsStore] = None):
        self.store = store or OperationsStore()
        self.integrity = StoreIntegrityManager()
        self.config = ConfigurationValidator()
        self.lifecycle = SystemLifecycleManager(self.store)
        self.health = OperationsHealthEngine(self.lifecycle, self.integrity)
        self.readiness = OperationsReadinessEngine(self.health, self.config, self.integrity, self.lifecycle)
        self.metrics = MetricsEngine()
        self.events = OperationalEventManager(self.store)
        self.jobs = JobLifecycleManager(self.store)
        self.incidents = IncidentEngine(self.store)
        self.backup = BackupEngine(store=self.store)
        self.recovery = RecoveryEngine(store=self.store)
        self.diagnostics = DiagnosticEngine(self.store, self.integrity, self.config, self.health)
        self.retention = RetentionEngine(self.store)

    def get_dashboard(self, tenant_id: Optional[str] = None) -> DashboardData:
        """Assembles a secure, multi-tenant aggregated operational dashboard snapshot."""
        lc_status = self.lifecycle.get_status()
        health_status = self.health.check_health()
        readiness_status = self.readiness.evaluate_readiness()
        metrics_summary = self.metrics.get_summary(tenant_id=tenant_id)

        # Active jobs & incidents
        jobs_list = self.jobs.list_jobs(tenant_id=tenant_id, limit=100)
        active_jobs = sum(1 for j in jobs_list if j.status in ["RUNNING", "QUEUED"])

        incidents_list = self.incidents.list_incidents(tenant_id=tenant_id, limit=100)
        open_incidents = sum(1 for i in incidents_list if i.status in ["OPEN", "INVESTIGATING"])

        # Latest backup
        backups = self.backup.list_backups()
        latest_bak = backups[0] if backups else None

        # Recent events
        events_list = self.events.list_events(tenant_id=tenant_id, limit=20)

        return DashboardData(
            lifecycle=lc_status,
            health=health_status,
            readiness=readiness_status,
            metrics=metrics_summary,
            active_jobs_count=active_jobs,
            open_incidents_count=open_incidents,
            latest_backup=latest_bak,
            recent_events=events_list,
        )
