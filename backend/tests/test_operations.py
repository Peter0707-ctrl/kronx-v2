"""
Phase 3.1 — Operations, Observability, Recovery & Lifecycle Control Test Suite
Contains 50+ comprehensive unit, integration, boundary, and adversarial security tests.
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

from auth.schemas import AuthenticationContext, UserRole
from operations.schemas import (
    LifecycleState,
    LifecycleStatus,
    HealthStatus,
    ReadinessDecision,
    Severity,
    JobStatus,
    IncidentStatus,
    EventType,
    RecoveryRequest,
)
from operations.errors import (
    OperationsError,
    LIFECYCLE_INVALID_TRANSITION,
    SYSTEM_DRAINING,
    SYSTEM_STOPPED,
    UNAUTHORIZED_OPERATION,
    JOB_NOT_FOUND,
    JOB_ALREADY_COMPLETED,
    BACKUP_NOT_FOUND,
    RECOVERY_BLOCKED,
)
from operations.orchestrator import OperationsOrchestrator
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
from api.operations import _orchestrator as api_orch

client = TestClient(app)


class TestOperationsSubsystem(unittest.TestCase):
    def setUp(self):
        api_orch.lifecycle.recover()
        self.tmp_dir = tempfile.mkdtemp(prefix="ops_test_")
        self.store_file = os.path.join(self.tmp_dir, "test_ops_store.json")
        self.backup_dir = os.path.join(self.tmp_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)


        self.store = OperationsStore(self.store_file)
        self.orchestrator = OperationsOrchestrator(self.store)

        # Re-point backup & recovery to isolated test directories
        self.orchestrator.backup.base_dir = self.tmp_dir
        self.orchestrator.backup.backup_dir = self.backup_dir
        self.orchestrator.recovery.base_dir = self.tmp_dir
        self.orchestrator.recovery.backup_dir = self.backup_dir
        self.orchestrator.integrity.base_dir = self.tmp_dir

        self.tenant_a = "tenant_alpha"
        self.tenant_b = "tenant_beta"
        self.ctx_a = AuthenticationContext(
            request_id="req_a",
            session_id="sess_a",
            user_id="usr_a",
            tenant_id=self.tenant_a,
            role=UserRole.USER,
        )
        self.ctx_operator = AuthenticationContext(
            request_id="req_op",
            session_id="sess_op",
            user_id="usr_op",
            tenant_id=self.tenant_a,
            role=UserRole.ADMIN,
        )

        # Create dummy store in temp dir for backup/recovery testing
        self.dummy_store_name = "workspace_store.json"
        self.dummy_store_path = os.path.join(self.tmp_dir, self.dummy_store_name)
        with open(self.dummy_store_path, "w", encoding="utf-8") as f:
            json.dump({"test_ws": {"id": "ws_1"}}, f)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            try:
                shutil.rmtree(self.tmp_dir)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # 1. Lifecycle State Machine Tests
    # ------------------------------------------------------------------
    def test_01_lifecycle_initial_state_ready(self):
        status = self.orchestrator.lifecycle.get_status()
        self.assertEqual(status.state, LifecycleState.READY)
        self.assertTrue(self.orchestrator.lifecycle.is_accepting_work())

    def test_02_lifecycle_transition_to_draining(self):
        status = self.orchestrator.lifecycle.drain(reason="Scheduled maintenance")
        self.assertEqual(status.state, LifecycleState.DRAINING)
        self.assertTrue(status.draining)
        self.assertFalse(self.orchestrator.lifecycle.is_accepting_work())

    def test_03_lifecycle_recovery_from_draining(self):
        self.orchestrator.lifecycle.drain()
        status = self.orchestrator.lifecycle.recover(reason="Maintenance completed")
        self.assertEqual(status.state, LifecycleState.READY)
        self.assertFalse(status.draining)

    def test_04_lifecycle_invalid_transition_rejected(self):
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.lifecycle.transition_to(LifecycleState.STOPPED)
        self.assertEqual(ctx.exception.code, LIFECYCLE_INVALID_TRANSITION)

    def test_05_lifecycle_drain_rejects_new_jobs(self):
        self.orchestrator.lifecycle.drain()
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.lifecycle.register_job("job_999")
        self.assertEqual(ctx.exception.code, SYSTEM_DRAINING)

    def test_06_lifecycle_stopped_rejects_jobs(self):
        self.orchestrator.lifecycle.stop()
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.lifecycle.register_job("job_1000")
        self.assertEqual(ctx.exception.code, SYSTEM_STOPPED)

    def test_07_lifecycle_job_accounting(self):
        self.orchestrator.lifecycle.register_job("job_1")
        self.orchestrator.lifecycle.register_job("job_2")
        self.assertEqual(self.orchestrator.lifecycle.get_status().active_jobs, 2)
        self.orchestrator.lifecycle.unregister_job("job_1")
        self.assertEqual(self.orchestrator.lifecycle.get_status().active_jobs, 1)

    # ------------------------------------------------------------------
    # 2. Metrics Engine & Bounded Cardinality
    # ------------------------------------------------------------------
    def test_08_metrics_increment_counters(self):
        self.orchestrator.metrics.increment("requests_total", value=5)
        self.orchestrator.metrics.increment("llm_tokens", value=250)
        summary = self.orchestrator.metrics.get_summary()
        self.assertEqual(summary["counters"]["requests_total"], 5)
        self.assertEqual(summary["counters"]["llm_tokens"], 250)

    def test_09_metrics_set_gauge(self):
        self.orchestrator.metrics.set_gauge("system_readiness_score", 9.5)
        summary = self.orchestrator.metrics.get_summary()
        self.assertEqual(summary["gauges"]["system_readiness_score"], 9.5)

    def test_10_metrics_bounded_name_sanitization(self):
        long_bad_name = "a" * 100 + "&&--$$"
        self.orchestrator.metrics.increment(long_bad_name, value=1)
        summary = self.orchestrator.metrics.get_summary()
        self.assertIn("custom_metric", summary["counters"])

    def test_11_metrics_tenant_scoped_summary(self):
        self.orchestrator.metrics.increment("requests_total", labels={"tenant_id": self.tenant_a})
        summary_a = self.orchestrator.metrics.get_summary(tenant_id=self.tenant_a)
        summary_b = self.orchestrator.metrics.get_summary(tenant_id=self.tenant_b)
        self.assertEqual(summary_a["tenant_activity_count"], 1)
        self.assertEqual(summary_b["tenant_activity_count"], 0)

    # ------------------------------------------------------------------
    # 3. Operational Events Engine
    # ------------------------------------------------------------------
    def test_12_event_emission_and_listing(self):
        evt = self.orchestrator.events.emit_event(
            event_type=EventType.REQUEST_STARTED,
            severity=Severity.LOW,
            tenant_id=self.tenant_a,
            metadata={"op": "scan"}
        )
        self.assertIsNotNone(evt.event_id)
        events = self.orchestrator.events.list_events(tenant_id=self.tenant_a)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, EventType.REQUEST_STARTED)

    def test_13_event_tenant_isolation(self):
        self.orchestrator.events.emit_event(
            event_type=EventType.AUTH_SUCCESS,
            tenant_id=self.tenant_a,
        )
        events_a = self.orchestrator.events.list_events(tenant_id=self.tenant_a)
        events_b = self.orchestrator.events.list_events(tenant_id=self.tenant_b)
        self.assertEqual(len(events_a), 1)
        self.assertEqual(len(events_b), 0)

    def test_14_event_metadata_secret_redaction(self):
        evt = self.orchestrator.events.emit_event(
            event_type=EventType.LLM_REQUEST,
            tenant_id=self.tenant_a,
            metadata={"key": "sk-1234567890abcdef1234567890", "token": "Bearer secret_token_value_long_123"}
        )
        self.assertNotIn("sk-1234567890", str(evt.metadata))
        self.assertIn("[REDACTED_API_KEY]", str(evt.metadata))

    # ------------------------------------------------------------------
    # 4. Job Lifecycle & Cooperative Cancellation
    # ------------------------------------------------------------------
    def test_15_job_create_and_start(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "WORKSPACE_SCAN")
        self.assertEqual(job.status, JobStatus.QUEUED)
        started = self.orchestrator.jobs.start_job(self.tenant_a, job.job_id)
        self.assertEqual(started.status, JobStatus.RUNNING)

    def test_16_job_update_progress(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "AI_PLAN")
        updated = self.orchestrator.jobs.update_progress(self.tenant_a, job.job_id, 0.75)
        self.assertEqual(updated.progress, 0.75)

    def test_17_job_complete(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "VERIFICATION")
        completed = self.orchestrator.jobs.complete_job(self.tenant_a, job.job_id, {"result": "PASSED"})
        self.assertEqual(completed.status, JobStatus.COMPLETED)
        self.assertEqual(completed.progress, 1.0)
        self.assertIsNotNone(completed.completed_at)

    def test_18_job_fail(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "LLM_INFERENCE")
        failed = self.orchestrator.jobs.fail_job(self.tenant_a, job.job_id, "Quota exhausted.")
        self.assertEqual(failed.status, JobStatus.FAILED)
        self.assertEqual(failed.error, "Quota exhausted.")

    def test_19_job_cancel(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "AGENT_JOB")
        cancelled = self.orchestrator.jobs.cancel_job(self.tenant_a, job.job_id)
        self.assertEqual(cancelled.status, JobStatus.CANCELLED)

    def test_20_job_cancel_already_completed_error(self):
        job = self.orchestrator.jobs.create_job(self.tenant_a, "AGENT_JOB")
        self.orchestrator.jobs.complete_job(self.tenant_a, job.job_id)
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.jobs.cancel_job(self.tenant_a, job.job_id)
        self.assertEqual(ctx.exception.code, JOB_ALREADY_COMPLETED)

    def test_21_job_cross_tenant_access_blocked(self):
        job_a = self.orchestrator.jobs.create_job(self.tenant_a, "SCAN")
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.jobs.get_job(self.tenant_b, job_a.job_id)
        self.assertEqual(ctx.exception.code, JOB_NOT_FOUND)

    # ------------------------------------------------------------------
    # 5. Incident Management & Automated Triggers
    # ------------------------------------------------------------------
    def test_22_incident_create_and_resolve(self):
        inc = self.orchestrator.incidents.create_incident(
            title="Database Latency Spike",
            description="Latency exceeded 500ms.",
            severity=Severity.MEDIUM,
            tenant_id=self.tenant_a,
        )
        self.assertEqual(inc.status, IncidentStatus.OPEN)
        resolved = self.orchestrator.incidents.resolve_incident(inc.incident_id, "Capacity scaled up.")
        self.assertEqual(resolved.status, IncidentStatus.RESOLVED)
        self.assertIsNotNone(resolved.resolved_at)

    def test_23_incident_security_trigger_cross_tenant(self):
        inc = self.orchestrator.incidents.check_security_trigger("CROSS_TENANT_VIOLATION", {}, tenant_id=self.tenant_b)
        self.assertIsNotNone(inc)
        self.assertEqual(inc.severity, Severity.HIGH)

    def test_24_incident_security_trigger_role_escalation(self):
        inc = self.orchestrator.incidents.check_security_trigger("ROLE_ESCALATION_ATTEMPT", {}, tenant_id=self.tenant_b)
        self.assertIsNotNone(inc)
        self.assertEqual(inc.severity, Severity.CRITICAL)

    def test_25_incident_tenant_isolation(self):
        self.orchestrator.incidents.create_incident(
            title="Tenant A Incident",
            description="Desc",
            severity=Severity.LOW,
            tenant_id=self.tenant_a,
        )
        incs_a = self.orchestrator.incidents.list_incidents(tenant_id=self.tenant_a)
        incs_b = self.orchestrator.incidents.list_incidents(tenant_id=self.tenant_b)
        self.assertEqual(len(incs_a), 1)
        self.assertEqual(len(incs_b), 0)

    # ------------------------------------------------------------------
    # 6. Persistent Store Integrity & Recovery Engine
    # ------------------------------------------------------------------
    def test_26_store_integrity_clean_verification(self):
        record = self.orchestrator.integrity.check_store(self.dummy_store_name)
        self.assertTrue(record.exists)
        self.assertTrue(record.valid_json)
        self.assertFalse(record.corrupted)
        self.assertTrue(len(record.sha256) > 0)

    def test_27_store_integrity_corruption_detection(self):
        corrupt_name = "corrupt_store.json"
        corrupt_path = os.path.join(self.tmp_dir, corrupt_name)
        with open(corrupt_path, "w", encoding="utf-8") as f:
            f.write("{ broken json non-parseable")

        rec = self.orchestrator.integrity.check_store(corrupt_name)
        self.assertTrue(rec.corrupted)
        self.assertFalse(rec.valid_json)

    def test_28_backup_creation_verified(self):
        bak = self.orchestrator.backup.create_backup(self.dummy_store_name, tenant_scope=self.tenant_a)
        self.assertIsNotNone(bak.backup_id)
        self.assertEqual(bak.status, "COMPLETED")
        self.assertTrue(os.path.exists(os.path.join(self.backup_dir, bak.backup_filename)))

    def test_29_backup_unapproved_file_rejected(self):
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.backup.create_backup(".env")
        self.assertEqual(ctx.exception.code, UNAUTHORIZED_OPERATION)

    def test_30_recovery_atomic_restore(self):
        # 1. Create backup
        bak = self.orchestrator.backup.create_backup(self.dummy_store_name)

        # 2. Corrupt store on disk
        with open(self.dummy_store_path, "w", encoding="utf-8") as f:
            f.write("corrupted content")

        # 3. Restore
        req = RecoveryRequest(backup_id=bak.backup_id, store_name=self.dummy_store_name)
        res = self.orchestrator.recovery.restore_backup(req, operator_role="OPERATOR")
        self.assertEqual(res.status, "SUCCESS")
        self.assertTrue(res.verification_passed)

        # 4. Verify store is restored
        with open(self.dummy_store_path, "r", encoding="utf-8") as f:
            restored_data = json.load(f)
        self.assertIn("test_ws", restored_data)

    def test_31_recovery_hash_mismatch_blocked(self):
        bak = self.orchestrator.backup.create_backup(self.dummy_store_name)
        bak_path = os.path.join(self.backup_dir, bak.backup_filename)

        # Tamper with backup file
        with open(bak_path, "w", encoding="utf-8") as f:
            f.write("tampered data")

        req = RecoveryRequest(backup_id=bak.backup_id, store_name=self.dummy_store_name)
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.recovery.restore_backup(req, operator_role="OPERATOR")
        self.assertEqual(ctx.exception.code, RECOVERY_BLOCKED)

    def test_32_recovery_unauthorized_user_role_blocked(self):
        bak = self.orchestrator.backup.create_backup(self.dummy_store_name)
        req = RecoveryRequest(backup_id=bak.backup_id, store_name=self.dummy_store_name)
        with self.assertRaises(OperationsError) as ctx:
            self.orchestrator.recovery.restore_backup(req, operator_role="USER")
        self.assertEqual(ctx.exception.code, UNAUTHORIZED_OPERATION)

    # ------------------------------------------------------------------
    # 7. Safe Diagnostics Engine
    # ------------------------------------------------------------------
    def test_33_diagnostics_run_clean(self):
        report = self.orchestrator.diagnostics.run_diagnostics()
        self.assertIsNotNone(report.diagnostic_id)
        self.assertEqual(report.failed_checks, 0)
        self.assertEqual(report.system_health, HealthStatus.HEALTHY)

    def test_34_diagnostics_no_secret_leakage(self):
        report = self.orchestrator.diagnostics.run_diagnostics()
        rep_json = json.dumps(report.model_dump())
        self.assertNotIn("sk-", rep_json)
        self.assertNotIn("password=", rep_json)

    # ------------------------------------------------------------------
    # 8. Configuration Validation
    # ------------------------------------------------------------------
    def test_35_configuration_validation_clean(self):
        cfg = self.orchestrator.config.validate()
        self.assertTrue(cfg.is_valid)
        self.assertEqual(cfg.status, HealthStatus.HEALTHY)
        # Verify boolean flags returned, never keys
        self.assertIn(cfg.summary.get("GEMINI_PROVIDER_CONFIGURED"), ["true", "false"])

    # ------------------------------------------------------------------
    # 9. Health & Readiness Evaluators
    # ------------------------------------------------------------------
    def test_36_health_check_healthy(self):
        res = self.orchestrator.health.check_health()
        self.assertEqual(res.status, HealthStatus.HEALTHY)
        self.assertIn("lifecycle", res.components)
        self.assertIn("stores", res.components)

    def test_37_readiness_evaluation_ready(self):
        res = self.orchestrator.readiness.evaluate_readiness()
        self.assertEqual(res.decision, ReadinessDecision.READY)
        self.assertEqual(res.score, 10.0)

    def test_38_readiness_fail_closed_when_stopped(self):
        self.orchestrator.lifecycle.stop()
        res = self.orchestrator.readiness.evaluate_readiness()
        self.assertEqual(res.decision, ReadinessDecision.BLOCKED)

    # ------------------------------------------------------------------
    # 10. Retention & Cleanup Engine
    # ------------------------------------------------------------------
    def test_39_retention_cleanup_execution(self):
        res = self.orchestrator.retention.run_retention_cleanup()
        self.assertIn("pruned_events", res)
        self.assertIn("pruned_jobs", res)

    # ------------------------------------------------------------------
    # 11. Aggregated Operational Dashboard
    # ------------------------------------------------------------------
    def test_40_dashboard_aggregation(self):
        dash = self.orchestrator.get_dashboard(tenant_id=self.tenant_a)
        self.assertEqual(dash.lifecycle.state, LifecycleState.READY)
        self.assertEqual(dash.health.status, HealthStatus.HEALTHY)
        self.assertIsNotNone(dash.readiness.decision)

    # ------------------------------------------------------------------
    # 12. REST API Endpoints Boundary Verification
    # ------------------------------------------------------------------
    def test_41_api_get_status(self):
        resp = client.get("/api/operations/status")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["state"], "READY")

    def test_42_api_get_metrics(self):
        resp = client.get("/api/operations/metrics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("counters", resp.json())

    def test_43_api_get_events(self):
        resp = client.get("/api/operations/events")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_44_api_diagnostics_unauthorized_user(self):
        resp = client.post("/api/operations/diagnostics/run")
        # Default user is not operator, expected 403
        self.assertEqual(resp.status_code, 403)

    def test_45_api_configuration_status(self):
        resp = client.get("/api/operations/configuration/status")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["is_valid"])

    def test_46_api_dashboard_endpoint(self):
        resp = client.get("/api/operations/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("lifecycle", resp.json())

    def test_47_api_jobs_list(self):
        resp = client.get("/api/operations/jobs")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_48_api_incidents_list(self):
        resp = client.get("/api/operations/incidents")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    # ------------------------------------------------------------------
    # 13. Concurrency & Stress Invariants
    # ------------------------------------------------------------------
    def test_49_concurrent_metrics_updates(self):
        def worker(i):
            self.orchestrator.metrics.increment("requests_total", value=1)
            self.orchestrator.metrics.increment("llm_tokens", value=10)

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(worker, range(50)))

        summary = self.orchestrator.metrics.get_summary()
        self.assertEqual(summary["counters"]["requests_total"], 50)
        self.assertEqual(summary["counters"]["llm_tokens"], 500)

    def test_50_concurrent_job_creation_isolation(self):
        def worker(i):
            t_id = f"t_{i % 5}"
            j = self.orchestrator.jobs.create_job(t_id, "TASK")
            self.orchestrator.jobs.complete_job(t_id, j.job_id)

        with ThreadPoolExecutor(max_workers=20) as pool:
            list(pool.map(worker, range(30)))

        jobs_t0 = self.orchestrator.jobs.list_jobs("t_0")
        self.assertEqual(len(jobs_t0), 6)


if __name__ == "__main__":
    unittest.main()
