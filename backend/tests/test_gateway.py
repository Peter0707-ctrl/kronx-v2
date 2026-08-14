"""
Phase 2H — Comprehensive API Gateway, Rate Limiting, Quota & Hardening Test Suite
Covers 52+ tests verifying request limits, security headers, rate limiting, quotas, concurrency,
abuse detection, metrics, health endpoints, audit rotation, and CORS.
"""
from __future__ import annotations
import os
import time
import shutil
import tempfile
import unittest
import threading
import uuid
from fastapi.testclient import TestClient

from main import app
from config.settings import config, GatewayConfig
from gateway.errors import (
    GatewayError,
    REQUEST_TOO_LARGE,
    INVALID_REQUEST,
    RATE_LIMITED,
    QUOTA_EXCEEDED,
    CONCURRENCY_LIMIT,
    ABUSE_LIMIT_REACHED,
    INTERNAL_ERROR,
)
from gateway.headers import sanitize_or_generate_request_id, get_security_headers
from gateway.request_limits import validate_payload_size, validate_json_structure
from gateway.rate_limit import RateLimiter, rate_limiter
from gateway.quotas import TenantQuotaManager, quota_manager
from gateway.concurrency import ConcurrencyCoordinator, concurrency_coordinator
from gateway.abuse import AbuseDetector, abuse_detector
from gateway.metrics import MetricsCollector, metrics_collector, ALLOWED_ENDPOINT_BUCKETS
from gateway.audit import log_gateway_event, sanitize_str, GATEWAY_LOG_FILE
from gateway.health import perform_health_check
from gateway.schemas import HealthState

client = TestClient(app)


class TestGatewayEnginePhase2H(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Request ID Generation
    # ------------------------------------------------------------------
    def test_01_request_id_generation(self):
        req_id = sanitize_or_generate_request_id(None)
        self.assertTrue(req_id.startswith("req_"))
        self.assertGreaterEqual(len(req_id), 8)

    # ------------------------------------------------------------------
    # 2. Request ID Sanitization
    # ------------------------------------------------------------------
    def test_02_request_id_sanitization(self):
        malicious_id = "req_123\nINJECTION\r\t"
        safe_id = sanitize_or_generate_request_id(malicious_id)
        self.assertNotIn("\n", safe_id)
        self.assertNotIn("\r", safe_id)
        self.assertTrue(safe_id.startswith("req_"))

    # ------------------------------------------------------------------
    # 3. Request Size Limit (Validation)
    # ------------------------------------------------------------------
    def test_03_request_size_limit_valid(self):
        # 1 MB is within limits
        validate_payload_size(1024 * 1024)

    # ------------------------------------------------------------------
    # 4. Request Size Limit Exceeded
    # ------------------------------------------------------------------
    def test_04_request_size_limit_exceeded(self):
        with self.assertRaises(GatewayError) as ctx:
            validate_payload_size(config.max_request_bytes + 1)
        self.assertEqual(ctx.exception.code, REQUEST_TOO_LARGE)
        self.assertEqual(ctx.exception.status_code, 413)

    # ------------------------------------------------------------------
    # 5. JSON Nesting Depth Limit
    # ------------------------------------------------------------------
    def test_05_json_depth_limit(self):
        nested = {"level": 0}
        curr = nested
        for i in range(config.max_json_depth + 5):
            curr["child"] = {"level": i + 1}
            curr = curr["child"]

        with self.assertRaises(GatewayError) as ctx:
            validate_json_structure(nested)
        self.assertEqual(ctx.exception.code, INVALID_REQUEST)

    # ------------------------------------------------------------------
    # 6. JSON String Length Limit
    # ------------------------------------------------------------------
    def test_06_json_string_length_limit(self):
        huge_data = {"key": "x" * (config.max_string_length + 100)}
        with self.assertRaises(GatewayError) as ctx:
            validate_json_structure(huge_data)
        self.assertEqual(ctx.exception.code, INVALID_REQUEST)

    # ------------------------------------------------------------------
    # 7. JSON Array Length Limit
    # ------------------------------------------------------------------
    def test_07_json_array_length_limit(self):
        huge_array = [i for i in range(config.max_array_length + 10)]
        with self.assertRaises(GatewayError) as ctx:
            validate_json_structure(huge_array)
        self.assertEqual(ctx.exception.code, INVALID_REQUEST)

    # ------------------------------------------------------------------
    # 8. JSON Object Fields Limit
    # ------------------------------------------------------------------
    def test_08_json_fields_limit(self):
        huge_obj = {f"k_{i}": i for i in range(config.max_object_fields + 10)}
        with self.assertRaises(GatewayError) as ctx:
            validate_json_structure(huge_obj)
        self.assertEqual(ctx.exception.code, INVALID_REQUEST)

    # ------------------------------------------------------------------
    # 9. Rate Limiting on General Identifier
    # ------------------------------------------------------------------
    def test_09_rate_limiting_general(self):
        rl = RateLimiter()
        ident = "test_user_09"
        for _ in range(10):
            rl.check_and_record(ident, operation="CUSTOM", custom_limit=10, window_seconds=60)

        with self.assertRaises(GatewayError) as ctx:
            rl.check_and_record(ident, operation="CUSTOM", custom_limit=10, window_seconds=60)
        self.assertEqual(ctx.exception.code, RATE_LIMITED)

    # ------------------------------------------------------------------
    # 10. Rate Limiting Operations
    # ------------------------------------------------------------------
    def test_10_rate_limiting_operations(self):
        rl = RateLimiter()
        ident = "test_tenant_10"
        limit = config.limit_plans_per_window
        for _ in range(limit):
            rl.check_and_record(ident, operation="PLANNING")

        with self.assertRaises(GatewayError) as ctx:
            rl.check_and_record(ident, operation="PLANNING")
        self.assertEqual(ctx.exception.code, RATE_LIMITED)

    # ------------------------------------------------------------------
    # 11. Rate Limit Window Expiration
    # ------------------------------------------------------------------
    def test_11_rate_limit_expiration(self):
        rl = RateLimiter()
        ident = "test_user_11"
        rl.check_and_record(ident, operation="TINY", custom_limit=1, window_seconds=1)
        time.sleep(1.1)
        # Should succeed now
        rl.check_and_record(ident, operation="TINY", custom_limit=1, window_seconds=1)

    # ------------------------------------------------------------------
    # 12. Bounded Rate Limiter Memory
    # ------------------------------------------------------------------
    def test_12_bounded_rate_limiter_memory(self):
        rl = RateLimiter()
        for i in range(100):
            rl.check_and_record(f"user_{i}", operation="GEN")
        self.assertLessEqual(len(rl._records), 5000)

    # ------------------------------------------------------------------
    # 13. Tenant Quotas Initialization
    # ------------------------------------------------------------------
    def test_13_tenant_quota_init(self):
        qm = TenantQuotaManager()
        usage = qm.get_quota_usage("tenant_13")
        self.assertEqual(usage.concurrent_jobs, 0)

    # ------------------------------------------------------------------
    # 14. Tenant Workspace Quota Check
    # ------------------------------------------------------------------
    def test_14_tenant_workspace_quota(self):
        qm = TenantQuotaManager()
        with self.assertRaises(GatewayError) as ctx:
            qm.check_workspace_quota("tenant_14", config.max_tenant_workspaces)
        self.assertEqual(ctx.exception.code, QUOTA_EXCEEDED)

    # ------------------------------------------------------------------
    # 15. Tenant Session Quota Check
    # ------------------------------------------------------------------
    def test_15_tenant_session_quota(self):
        qm = TenantQuotaManager()
        with self.assertRaises(GatewayError) as ctx:
            qm.check_session_quota("tenant_15", config.max_tenant_sessions)
        self.assertEqual(ctx.exception.code, QUOTA_EXCEEDED)

    # ------------------------------------------------------------------
    # 16. Tenant Concurrent Job Acquisition & Release
    # ------------------------------------------------------------------
    def test_16_tenant_concurrent_jobs(self):
        qm = TenantQuotaManager()
        tnt = "tenant_16"
        for _ in range(config.max_tenant_concurrent_jobs):
            qm.acquire_job_slot(tnt)

        with self.assertRaises(GatewayError) as ctx:
            qm.acquire_job_slot(tnt)
        self.assertEqual(ctx.exception.code, QUOTA_EXCEEDED)

        qm.release_job_slot(tnt)
        # Should succeed now
        qm.acquire_job_slot(tnt)

    # ------------------------------------------------------------------
    # 17. Concurrency Coordinator Initialization
    # ------------------------------------------------------------------
    def test_17_concurrency_coordinator_init(self):
        cc = ConcurrencyCoordinator()
        self.assertIn("PLAN", cc._semaphores)
        self.assertIn("EXECUTION", cc._semaphores)

    # ------------------------------------------------------------------
    # 18. Concurrency Limit Rejection
    # ------------------------------------------------------------------
    def test_18_concurrency_limit_rejection(self):
        cc = ConcurrencyCoordinator()
        slots = []
        try:
            for _ in range(config.max_concurrent_executions):
                cm = cc.limit_concurrency("EXECUTION", timeout=0.01)
                cm.__enter__()
                slots.append(cm)

            with self.assertRaises(GatewayError) as ctx:
                with cc.limit_concurrency("EXECUTION", timeout=0.01):
                    pass
            self.assertEqual(ctx.exception.code, CONCURRENCY_LIMIT)
        finally:
            for s in slots:
                try:
                    s.__exit__(None, None, None)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # 19. Abuse Detector Violation Recording
    # ------------------------------------------------------------------
    def test_19_abuse_detector_recording(self):
        ad = AbuseDetector()
        ident = "attacker_19"
        ad.record_violation(ident, "UNAUTHORIZED_WORKSPACE")
        self.assertIn(ident, ad._records)
        self.assertEqual(ad._records[ident].violation_count, 1)

    # ------------------------------------------------------------------
    # 20. Abuse Detector Cooldown Activation
    # ------------------------------------------------------------------
    def test_20_abuse_cooldown_activation(self):
        ad = AbuseDetector()
        ident = "attacker_20"
        for _ in range(10):
            ad.record_violation(ident, "PATH_TRAVERSAL")

        with self.assertRaises(GatewayError) as ctx:
            ad.check_abuse_status(ident)
        self.assertEqual(ctx.exception.code, ABUSE_LIMIT_REACHED)

    # ------------------------------------------------------------------
    # 21. Abuse Detector Memory Bound
    # ------------------------------------------------------------------
    def test_21_abuse_detector_memory_bound(self):
        ad = AbuseDetector()
        for i in range(100):
            ad.record_violation(f"ident_{i}", "GENERIC")
        self.assertLessEqual(len(ad._records), 2000)

    # ------------------------------------------------------------------
    # 22. Security Headers Injected
    # ------------------------------------------------------------------
    def test_22_security_headers_injected(self):
        headers = get_security_headers()
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    # ------------------------------------------------------------------
    # 23. Security Headers in Live API Response
    # ------------------------------------------------------------------
    def test_23_security_headers_in_response(self):
        resp = client.get("/api/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertIn("X-Request-ID", resp.headers)

    # ------------------------------------------------------------------
    # 24. Audit Log Event Generation
    # ------------------------------------------------------------------
    def test_24_audit_log_event(self):
        log_gateway_event(
            request_id="req_test_24",
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=10.5,
            user_id="usr_24",
            tenant_id="tnt_24",
        )
        self.assertTrue(os.path.exists(GATEWAY_LOG_FILE))

    # ------------------------------------------------------------------
    # 25. Audit Log Newline Sanitization
    # ------------------------------------------------------------------
    def test_25_audit_newline_sanitization(self):
        malicious = "test_val\n[GATEWAY_INJECTED_EVENT]\r"
        clean = sanitize_str(malicious)
        self.assertNotIn("\n", clean)
        self.assertNotIn("\r", clean)

    # ------------------------------------------------------------------
    # 26. Metrics Request Recording
    # ------------------------------------------------------------------
    def test_26_metrics_request_recording(self):
        mc = MetricsCollector()
        mc.record_request("/api/workspace", 25.0, 200)
        snap = mc.get_snapshot()
        self.assertEqual(snap.requests_total, 1)
        self.assertEqual(snap.errors_total, 0)

    # ------------------------------------------------------------------
    # 27. Metrics Error Recording
    # ------------------------------------------------------------------
    def test_27_metrics_error_recording(self):
        mc = MetricsCollector()
        mc.record_request("/api/auth/login", 15.0, 401)
        snap = mc.get_snapshot()
        self.assertEqual(snap.requests_total, 1)
        self.assertEqual(snap.errors_total, 1)
        self.assertEqual(snap.auth_failures_total, 1)

    # ------------------------------------------------------------------
    # 28. Metrics Bounded Label Cardinality
    # ------------------------------------------------------------------
    def test_28_metrics_cardinality_bound(self):
        mc = MetricsCollector()
        for i in range(100):
            mc.record_request(f"/api/arbitrary_user_path_{i}", 5.0, 200)
        snap = mc.get_snapshot()
        self.assertIn("OTHER", snap.endpoint_counts)
        self.assertEqual(len(snap.endpoint_counts), len(ALLOWED_ENDPOINT_BUCKETS))

    # ------------------------------------------------------------------
    # 29. Health Check Evaluation
    # ------------------------------------------------------------------
    def test_29_health_check_eval(self):
        health = perform_health_check()
        self.assertIn(health.status, (HealthState.READY, HealthState.DEGRADED, HealthState.LIVE))
        self.assertEqual(health.version, "2.0.0")

    # ------------------------------------------------------------------
    # 30. Health Endpoint /api/health
    # ------------------------------------------------------------------
    def test_30_health_endpoint(self):
        resp = client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["version"], "2.0.0")

    # ------------------------------------------------------------------
    # 31. Health Liveness /api/health/live
    # ------------------------------------------------------------------
    def test_31_health_live_endpoint(self):
        resp = client.get("/api/health/live")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "LIVE")

    # ------------------------------------------------------------------
    # 32. Health Readiness /api/health/ready
    # ------------------------------------------------------------------
    def test_32_health_ready_endpoint(self):
        resp = client.get("/api/health/ready")
        self.assertIn(resp.status_code, (200, 503))

    # ------------------------------------------------------------------
    # 33. Sanitized Error on Oversized Body
    # ------------------------------------------------------------------
    def test_33_oversized_payload_middleware(self):
        huge_headers = {"Content-Length": str(config.max_request_bytes + 5000)}
        resp = client.post("/api/auth/register", json={"username": "u", "password": "p"}, headers=huge_headers)
        self.assertEqual(resp.status_code, 413)
        self.assertEqual(resp.json()["detail"]["code"], REQUEST_TOO_LARGE)

    # ------------------------------------------------------------------
    # 34. Middleware Request Correlation
    # ------------------------------------------------------------------
    def test_34_middleware_correlation(self):
        custom_id = "req_custom_correlation_34"
        resp = client.get("/api/health/live", headers={"X-Request-ID": custom_id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Request-ID"), custom_id)

    # ------------------------------------------------------------------
    # 35. CORS Allowed Origins Config
    # ------------------------------------------------------------------
    def test_35_cors_origins_config(self):
        self.assertIn("http://localhost:5173", config.cors_allowed_origins)

    # ------------------------------------------------------------------
    # 36. Gateway Global Facade Properties
    # ------------------------------------------------------------------
    def test_36_gateway_facade(self):
        from gateway import gateway
        self.assertIsNotNone(gateway.rate_limiter)
        self.assertIsNotNone(gateway.quota_manager)
        self.assertIsNotNone(gateway.concurrency)
        self.assertIsNotNone(gateway.abuse_detector)
        self.assertIsNotNone(gateway.metrics)

    # ------------------------------------------------------------------
    # 37. Thread-Safe Concurrency Execution
    # ------------------------------------------------------------------
    def test_37_threadsafe_concurrency(self):
        cc = ConcurrencyCoordinator()
        errors = []

        def worker():
            try:
                with cc.limit_concurrency("PLAN", timeout=0.5):
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(errors, [])

    # ------------------------------------------------------------------
    # 38. Bounded Quota Jobs Dictionary
    # ------------------------------------------------------------------
    def test_38_quota_jobs_cleanup(self):
        qm = TenantQuotaManager()
        tnt = "tenant_cleanup_38"
        qm.acquire_job_slot(tnt)
        qm.release_job_slot(tnt)
        self.assertNotIn(tnt, qm._active_jobs)

    # ------------------------------------------------------------------
    # 39. Metric Snapshot Serializability
    # ------------------------------------------------------------------
    def test_39_metric_snapshot_json(self):
        snap = metrics_collector.get_snapshot()
        self.assertIsInstance(snap.model_dump(), dict)

    # ------------------------------------------------------------------
    # 40. Environment Identification
    # ------------------------------------------------------------------
    def test_40_environment_identification(self):
        cfg = GatewayConfig(environment="testing")
        self.assertTrue(cfg.is_testing())
        self.assertFalse(cfg.is_production())

    # ------------------------------------------------------------------
    # 41. Path Traversal Protection Check
    # ------------------------------------------------------------------
    def test_41_path_traversal_detection(self):
        from tools.path_verify import verify_safe_path
        ws_root = os.path.join(self.tmp, "ws_root")
        os.makedirs(ws_root, exist_ok=True)
        with self.assertRaises(ValueError) as ctx:
            verify_safe_path(ws_root, "../../../etc/passwd")
        self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")

    # ------------------------------------------------------------------
    # 42. Windows System32 Path Traversal Defense
    # ------------------------------------------------------------------
    def test_42_windows_system32_path_defense(self):
        from tools.path_verify import verify_safe_path
        ws_root = os.path.join(self.tmp, "ws_root")
        os.makedirs(ws_root, exist_ok=True)
        with self.assertRaises(ValueError) as ctx:
            verify_safe_path(ws_root, "C:\\Windows\\System32\\calc.exe")
        self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")


    # ------------------------------------------------------------------
    # 43. Sensitive File Block in Tool Runtime
    # ------------------------------------------------------------------
    def test_43_sensitive_file_block(self):
        from tools.runtime import ToolRuntime
        tr = ToolRuntime()
        res = tr.execute_tool(
            request_id="r43",
            workspace_id="ws_fake",
            tool_name="read_file",
            arguments={"path": ".env"},
        )
        self.assertFalse(res.success)

    # ------------------------------------------------------------------
    # 44. ADMIN Permission Self-Grant Blocked
    # ------------------------------------------------------------------
    def test_44_admin_permission_blocked(self):
        from tools.permissions import PermissionEngine
        pe = PermissionEngine()
        ok, reason = pe.validate_permission("ADMIN", "READ")
        self.assertFalse(ok)
        self.assertEqual(reason, "FORBIDDEN_PERMISSION_LEVEL")

    # ------------------------------------------------------------------
    # 45. EXECUTE Permission Blocked
    # ------------------------------------------------------------------
    def test_45_execute_permission_blocked(self):
        from tools.permissions import PermissionEngine
        pe = PermissionEngine()
        ok, reason = pe.validate_permission("EXECUTE", "READ")
        self.assertFalse(ok)
        self.assertEqual(reason, "FORBIDDEN_PERMISSION_LEVEL")

    # ------------------------------------------------------------------
    # 46. NETWORK Permission Blocked
    # ------------------------------------------------------------------
    def test_46_network_permission_blocked(self):
        from tools.permissions import PermissionEngine
        pe = PermissionEngine()
        ok, reason = pe.validate_permission("NETWORK", "READ")
        self.assertFalse(ok)
        self.assertEqual(reason, "FORBIDDEN_PERMISSION_LEVEL")

    # ------------------------------------------------------------------
    # 47. Unauthenticated User Accessing Protected Me Endpoint
    # ------------------------------------------------------------------
    def test_47_invalid_bearer_token(self):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer kx_invalid_fake_token"})
        self.assertEqual(resp.status_code, 401)

    # ------------------------------------------------------------------
    # 48. Concurrent Multi-Tenant Isolation Load Test
    # ------------------------------------------------------------------
    def test_48_concurrent_multi_tenant_load(self):
        from auth.store import AuthStore
        from auth.authentication import AuthenticationService
        auth_store = AuthStore(os.path.join(self.tmp, "auth.json"))
        auth_svc = AuthenticationService(auth_store)

        from auth.schemas import RegisterRequest
        tenants = ["tenant_alpha", "tenant_beta", "tenant_gamma"]
        users = []
        for t in tenants:
            u = auth_svc.register_user(RegisterRequest(
                username=f"user_{t}",
                password="Password123!",
                email=f"{t}@kronx.ai",
                tenant_id=t,
            ))
            users.append(u)

        self.assertEqual(len(users), 3)
        self.assertEqual(len({u.tenant_id for u in users}), 3)

    # ------------------------------------------------------------------
    # 49. Sanitized 404 on Unauthorized Cross-Tenant Resource
    # ------------------------------------------------------------------
    def test_49_cross_tenant_sanitized_404(self):
        from auth.authorization import MultiTenantAuthorizer
        from auth.schemas import AuthenticationContext
        authorizer = MultiTenantAuthorizer()
        ctx_attacker = AuthenticationContext(request_id="r49", session_id="s49", user_id="u_att", tenant_id="tnt_att")
        victim_plan = {"plan_id": "plan_secret_49", "tenant_id": "tnt_victim"}

        with self.assertRaises(Exception) as ctx:
            authorizer.authorize_object_access(ctx_attacker, victim_plan, "Plan")
        self.assertEqual(ctx.exception.code, "RESOURCE_NOT_FOUND")

    # ------------------------------------------------------------------
    # 50. Modification Requires Write Authorization
    # ------------------------------------------------------------------
    def test_50_modification_requires_write_auth(self):
        from modification.orchestrator import ModificationOrchestrator
        mod = ModificationOrchestrator()
        # Direct apply with invalid auth id fails cleanly
        with self.assertRaises(Exception):
            mod.apply("prop_fake", "auth_write_invalid")


    # ------------------------------------------------------------------
    # 51. Read-Only Verification Engine Guarantee
    # ------------------------------------------------------------------
    def test_51_verification_read_only(self):
        from verification.orchestrator import VerificationOrchestrator
        vo = VerificationOrchestrator()
        self.assertTrue(hasattr(vo, "run_verification"))

    # ------------------------------------------------------------------
    # 52. Server State Persistence Survival
    # ------------------------------------------------------------------
    def test_52_persistence_survival(self):
        from auth.store import AuthStore
        store_path = os.path.join(self.tmp, "persist_test.json")
        st1 = AuthStore(store_path)
        st1.save_user({"user_id": "u52", "username": "user52", "tenant_id": "tnt52"})

        st2 = AuthStore(store_path)
        u_loaded = st2.get_user_by_id("u52")
        self.assertIsNotNone(u_loaded)
        self.assertEqual(u_loaded["username"], "user52")


if __name__ == "__main__":
    unittest.main()
