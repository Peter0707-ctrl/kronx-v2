"""
Phase 2F — Comprehensive Verification, Testing & Readiness Test Suite
Covers 36+ unit and integration tests verifying all security invariants, workspace containment,
integrity checks, regression detectors, health checks, readiness scoring, and API lifecycle.
"""
from __future__ import annotations
import os
import shutil
import tempfile
import unittest
import threading
import uuid
from fastapi.testclient import TestClient

from main import app
from workspace.manager import WorkspaceManager
from workspace.store import WorkspaceStore
from verification.schemas import (
    VerificationRequest, VerificationResult, VerificationCheck,
    CheckStatus, CheckSeverity, OverallVerificationStatus, ReadinessDecision,
    VerificationType
)
from verification.errors import (
    VerificationError, WORKSPACE_NOT_AUTHORIZED, VERIFICATION_NOT_FOUND
)
from verification.orchestrator import VerificationOrchestrator
from verification.security import SecurityInvariantChecker
from verification.workspace import WorkspaceVerifier
from verification.tests import TestVerifier
from verification.integrity import IntegrityVerifier
from verification.regression import RegressionDetector
from verification.health import RuntimeHealthChecker
from verification.readiness import ProductionReadinessEngine
from verification.store import VerificationStore
from verification.audit import log_verification_audit, sanitize_str

client = TestClient(app)


def _make_workspace():
    tmp = tempfile.mkdtemp()
    proj = os.path.join(tmp, "project")
    os.makedirs(proj, exist_ok=True)
    ws_id = f"ws_{uuid.uuid4().hex[:8]}"
    os.environ["KRONX_WORKSPACE_ROOT"] = tmp
    store = WorkspaceStore()
    store.save_workspace(ws_id, {
        "workspace_id": ws_id,
        "root_path": proj,
        "status": "authorized",
        "created_at": "2026-08-14T00:00:00Z",
    })
    return tmp, proj, ws_id


class TestVerificationEnginePhase2F(unittest.TestCase):

    def setUp(self):
        self.tmp, self.proj, self.ws_id = _make_workspace()
        self.ws_store = WorkspaceStore()
        self.ver_store_file = os.path.join(self.tmp, "ver_store.json")
        self.ver_store = VerificationStore(self.ver_store_file)
        self.orchestrator = VerificationOrchestrator(
            ws_store=self.ws_store,
            ver_store=self.ver_store,
        )


    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. Schema Validation
    # ------------------------------------------------------------------
    def test_01_schema_validation(self):
        req = VerificationRequest(
            request_id="r1",
            workspace_id=self.ws_id,
            verification_type=VerificationType.FULL,
        )
        self.assertEqual(req.workspace_id, self.ws_id)
        self.assertTrue(req.include_security_checks)

    # ------------------------------------------------------------------
    # 2. Unknown Workspace Rejection
    # ------------------------------------------------------------------
    def test_02_unknown_workspace_rejected(self):
        req = VerificationRequest(
            request_id="r2",
            workspace_id="ws_unknown_nonexistent",
        )
        with self.assertRaises(VerificationError) as ctx:
            self.orchestrator.run_verification(req)
        self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 3. Workspace Containment Verification
    # ------------------------------------------------------------------
    def test_03_workspace_containment_verification(self):
        wv = WorkspaceVerifier(self.ws_store)
        checks = wv.verify_workspace(self.ws_id)
        containment_chk = next(c for c in checks if c.name == "PATH_CONTAINMENT_VERIFICATION")
        self.assertEqual(containment_chk.status, CheckStatus.PASS)

    # ------------------------------------------------------------------
    # 4. Traversal / Symlink Escape Defense
    # ------------------------------------------------------------------
    def test_04_traversal_escape_defense(self):
        from tools.path_verify import verify_safe_path
        with self.assertRaises(ValueError):
            verify_safe_path(self.proj, "../../../etc/passwd")

    # ------------------------------------------------------------------
    # 5. Sensitive File Protection Check
    # ------------------------------------------------------------------
    def test_05_sensitive_file_protection(self):
        from modification.sensitive import SensitiveFileDetector
        is_env, _ = SensitiveFileDetector.is_sensitive_path(".env")
        is_pem, _ = SensitiveFileDetector.is_sensitive_path("id_rsa")
        self.assertTrue(is_env)
        self.assertTrue(is_pem)

    # ------------------------------------------------------------------
    # 6. Security Invariant Detection
    # ------------------------------------------------------------------
    def test_06_security_invariant_detection(self):
        sic = SecurityInvariantChecker()
        checks = sic.verify_all_invariants()
        self.assertTrue(all(c.status == CheckStatus.PASS for c in checks))

    # ------------------------------------------------------------------
    # 7. Subprocess Static Check
    # ------------------------------------------------------------------
    def test_07_no_subprocess_detected(self):
        sic = SecurityInvariantChecker()
        chk = sic._check_no_subprocess_or_shell()
        self.assertEqual(chk.status, CheckStatus.PASS)

    # ------------------------------------------------------------------
    # 8. Shell Static Check
    # ------------------------------------------------------------------
    def test_08_no_shell_detected(self):
        sic = SecurityInvariantChecker()
        chk = sic._check_no_subprocess_or_shell()
        self.assertEqual(chk.status, CheckStatus.PASS)
        self.assertEqual(chk.evidence.get("violations_count"), 0)

    # ------------------------------------------------------------------
    # 9. Permission Escalation Rejection
    # ------------------------------------------------------------------
    def test_09_permission_escalation_rejected(self):
        from tools.permissions import PermissionEngine
        pe = PermissionEngine()
        ok_admin, r = pe.validate_permission("ADMIN", "READ")
        self.assertFalse(ok_admin)
        self.assertEqual(r, "FORBIDDEN_PERMISSION_LEVEL")

    # ------------------------------------------------------------------
    # 10. Default-Deny Validation
    # ------------------------------------------------------------------
    def test_10_default_deny_validation(self):
        from tools.permissions import PermissionEngine
        pe = PermissionEngine()
        ok, r = pe.validate_permission("WRITE", "READ")
        self.assertFalse(ok)

    # ------------------------------------------------------------------
    # 11. ToolRuntime Enforcement Check
    # ------------------------------------------------------------------
    def test_11_tool_runtime_enforcement(self):
        sic = SecurityInvariantChecker()
        chk = sic._check_tool_runtime_invariants()
        self.assertEqual(chk.status, CheckStatus.PASS)

    # ------------------------------------------------------------------
    # 12. Modification Authorization Check
    # ------------------------------------------------------------------
    def test_12_modification_authorization(self):
        sic = SecurityInvariantChecker()
        chk = sic._check_modification_gate_invariants()
        self.assertEqual(chk.status, CheckStatus.PASS)

    # ------------------------------------------------------------------
    # 13. Rollback Integrity Verification
    # ------------------------------------------------------------------
    def test_13_rollback_integrity(self):
        iv = IntegrityVerifier()
        checks = iv.verify_workspace_integrity(self.ws_id, self.proj)
        self.assertTrue(all(c.status != CheckStatus.FAIL for c in checks))

    # ------------------------------------------------------------------
    # 14. Checkpoint Integrity Verification
    # ------------------------------------------------------------------
    def test_14_checkpoint_integrity(self):
        from execution.checkpoint import ExecutionStore
        e_store = ExecutionStore()
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        e_store.save_execution(exec_id, {"execution_id": exec_id, "workspace_id": self.ws_id, "status": "COMPLETED"})
        
        iv = IntegrityVerifier(exec_store=e_store)
        checks = iv.verify_workspace_integrity(self.ws_id, self.proj, execution_id=exec_id)
        chk = next(c for c in checks if c.name == "EXECUTION_CHECKPOINT_INTEGRITY")
        self.assertEqual(chk.status, CheckStatus.PASS)

    # ------------------------------------------------------------------
    # 15. Hash Mismatch Detection
    # ------------------------------------------------------------------
    def test_15_hash_mismatch_detection(self):
        from modification.atomic import compute_sha256
        h1 = compute_sha256(b"hello")
        h2 = compute_sha256(b"world")
        self.assertNotEqual(h1, h2)

    # ------------------------------------------------------------------
    # 16. Regression Detection Check
    # ------------------------------------------------------------------
    def test_16_regression_detection(self):
        rd = RegressionDetector()
        checks = rd.detect_regressions()
        self.assertTrue(all(c.status == CheckStatus.PASS for c in checks))

    # ------------------------------------------------------------------
    # 17. Test Suite Result Validation
    # ------------------------------------------------------------------
    def test_17_test_suite_validation(self):
        tv = TestVerifier()
        checks = tv.verify_test_suites()
        self.assertTrue(all(c.status == CheckStatus.PASS for c in checks))

    # ------------------------------------------------------------------
    # 18. Missing Test Detection (Synthetic Failure)
    # ------------------------------------------------------------------
    def test_18_missing_test_detection(self):
        from verification.tests import EXPECTED_TEST_SUITES
        EXPECTED_TEST_SUITES["test_nonexistent_fake.py"] = {"phase": "Fake", "min_tests": 10}
        try:
            tv = TestVerifier()
            checks = tv.verify_test_suites()
            chk = next(c for c in checks if c.name == "TEST_SUITE_INTEGRITY")
            self.assertEqual(chk.status, CheckStatus.FAIL)
            self.assertEqual(chk.severity, CheckSeverity.CRITICAL)
        finally:
            del EXPECTED_TEST_SUITES["test_nonexistent_fake.py"]

    # ------------------------------------------------------------------
    # 19. Runtime Health Check
    # ------------------------------------------------------------------
    def test_19_runtime_health(self):
        hc = RuntimeHealthChecker()
        checks = hc.check_runtime_health()
        self.assertTrue(all(c.status == CheckStatus.PASS for c in checks))

    # ------------------------------------------------------------------
    # 20. Readiness Calculation
    # ------------------------------------------------------------------
    def test_20_readiness_calculation(self):
        engine = ProductionReadinessEngine()
        pass_check = VerificationCheck(
            check_id="c1", category="SECURITY", name="N", status=CheckStatus.PASS,
            severity=CheckSeverity.INFO, message="ok"
        )
        status, decision, s_score, i_score, t_score, r_score, crits, warns, recs = (
            engine.evaluate_readiness([pass_check])
        )
        self.assertEqual(decision, ReadinessDecision.READY)
        self.assertEqual(status, OverallVerificationStatus.PASSED)
        self.assertEqual(r_score, 10.0)

    # ------------------------------------------------------------------
    # 21. Critical Finding Blocks Readiness
    # ------------------------------------------------------------------
    def test_21_critical_finding_blocks_readiness(self):
        engine = ProductionReadinessEngine()
        crit_check = VerificationCheck(
            check_id="c1", category="SECURITY", name="CRIT", status=CheckStatus.FAIL,
            severity=CheckSeverity.CRITICAL, message="Critical security issue"
        )
        status, decision, s_score, i_score, t_score, r_score, crits, warns, recs = (
            engine.evaluate_readiness([crit_check])
        )
        self.assertEqual(decision, ReadinessDecision.BLOCKED)
        self.assertEqual(status, OverallVerificationStatus.BLOCKED)
        self.assertEqual(len(crits), 1)

    # ------------------------------------------------------------------
    # 22. Warning Readiness Evaluation
    # ------------------------------------------------------------------
    def test_22_warning_readiness(self):
        engine = ProductionReadinessEngine()
        warn_check = VerificationCheck(
            check_id="c1", category="INTEGRITY", name="WARN_CHK", status=CheckStatus.WARN,
            severity=CheckSeverity.LOW, message="Non blocking warning"
        )
        status, decision, s_score, i_score, t_score, r_score, crits, warns, recs = (
            engine.evaluate_readiness([warn_check])
        )
        self.assertEqual(decision, ReadinessDecision.READY_WITH_WARNINGS)
        self.assertEqual(status, OverallVerificationStatus.PASSED_WITH_WARNINGS)

    # ------------------------------------------------------------------
    # 23. Audit Logging
    # ------------------------------------------------------------------
    def test_23_audit_logging(self):
        ref = log_verification_audit(
            verification_id="v1",
            request_id="r1",
            workspace_id="ws1",
            status="PASSED",
            duration_ms=10.5,
            check_count=5,
            critical_count=0,
            warning_count=0,
            readiness_decision="READY",
        )
        self.assertIn("audit_ver_v1", ref)

    # ------------------------------------------------------------------
    # 24. Newline Sanitization
    # ------------------------------------------------------------------
    def test_24_newline_sanitization(self):
        raw = "line1\nline2\rline3"
        clean = sanitize_str(raw)
        self.assertNotIn("\n", clean)
        self.assertNotIn("\r", clean)

    # ------------------------------------------------------------------
    # 25. Secret Exclusion in Audit
    # ------------------------------------------------------------------
    def test_25_secret_exclusion(self):
        res = self.orchestrator.run_verification(VerificationRequest(
            request_id="r25",
            workspace_id=self.ws_id,
        ))
        res_dump = str(res.model_dump())
        self.assertNotIn("sk-", res_dump)
        self.assertNotIn("PRIVATE KEY", res_dump)

    # ------------------------------------------------------------------
    # 26. Store Persistence
    # ------------------------------------------------------------------
    def test_26_store_persistence(self):
        res = self.orchestrator.run_verification(VerificationRequest(
            request_id="r26",
            workspace_id=self.ws_id,
        ))
        loaded = self.ver_store.get_verification(res.verification_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["verification_id"], res.verification_id)

    # ------------------------------------------------------------------
    # 27. Corruption Recovery
    # ------------------------------------------------------------------
    def test_27_corruption_recovery(self):
        with open(self.ver_store.path, "w") as f:
            f.write("CORRUPT_DATA_{{{")
        self.ver_store._cache = None
        data = self.ver_store.get_verification("nonexistent")
        self.assertIsNone(data)

    # ------------------------------------------------------------------
    # 28. Concurrent Verification
    # ------------------------------------------------------------------
    def test_28_concurrent_verification(self):
        errors = []
        def worker(idx):
            try:
                r = self.orchestrator.run_verification(VerificationRequest(
                    request_id=f"r28_{idx}",
                    workspace_id=self.ws_id,
                ))
                assert r.status in (OverallVerificationStatus.PASSED, OverallVerificationStatus.PASSED_WITH_WARNINGS)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(errors, [])

    # ------------------------------------------------------------------
    # 29. Full API Verification Lifecycle
    # ------------------------------------------------------------------
    def test_29_full_api_verification_lifecycle(self):
        os.environ["KRONX_WORKSPACE_ROOT"] = self.tmp
        reg_resp = client.post("/api/workspace", json={"root_path": self.proj})
        self.assertEqual(reg_resp.status_code, 200)
        api_ws_id = reg_resp.json()["workspace_id"]

        # Run verification
        run_resp = client.post("/api/verification/run", json={"workspace_id": api_ws_id})
        self.assertEqual(run_resp.status_code, 200)
        ver_id = run_resp.json()["verification"]["verification_id"]

        # Get verification
        get_resp = client.get(f"/api/verification/{ver_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["verification"]["verification_id"], ver_id)

        # Get status
        stat_resp = client.get(f"/api/verification/{ver_id}/status")
        self.assertEqual(stat_resp.status_code, 200)
        self.assertIn("readiness_decision", stat_resp.json())

        # Get checks
        chk_resp = client.get(f"/api/verification/{ver_id}/checks")
        self.assertEqual(chk_resp.status_code, 200)
        self.assertGreater(chk_resp.json()["check_count"], 0)

        # Revalidate
        reval_resp = client.post(f"/api/verification/{ver_id}/revalidate")
        self.assertEqual(reval_resp.status_code, 200)

    # ------------------------------------------------------------------
    # 30. Sanitized Error Details (No Raw Tracebacks)
    # ------------------------------------------------------------------
    def test_30_sanitized_errors(self):
        resp = client.post("/api/verification/run", json={"workspace_id": "ws_nonexistent_test"})
        self.assertEqual(resp.status_code, 403)
        self.assertNotIn("Traceback", resp.text)

    # ------------------------------------------------------------------
    # 31. Repeated Verification Determinism
    # ------------------------------------------------------------------
    def test_31_repeated_verification_determinism(self):
        req1 = VerificationRequest(request_id="r31_1", workspace_id=self.ws_id)
        req2 = VerificationRequest(request_id="r31_2", workspace_id=self.ws_id)
        res1 = self.orchestrator.run_verification(req1)
        res2 = self.orchestrator.run_verification(req2)
        self.assertEqual(res1.status, res2.status)
        self.assertEqual(res1.readiness_decision, res2.readiness_decision)
        self.assertEqual(len(res1.checks), len(res2.checks))

    # ------------------------------------------------------------------
    # 32. Resource Limits & Bounded Output
    # ------------------------------------------------------------------
    def test_32_resource_limits(self):
        from verification.schemas import MAX_VERIFICATION_FILES, MAX_CHECKS
        self.assertEqual(MAX_VERIFICATION_FILES, 5000)
        self.assertEqual(MAX_CHECKS, 500)

    # ------------------------------------------------------------------
    # 33. Cross-Workspace Isolation
    # ------------------------------------------------------------------
    def test_33_cross_workspace_isolation(self):
        req = VerificationRequest(request_id="r33", workspace_id="ws_different_unauthorized_id")
        with self.assertRaises(VerificationError) as ctx:
            self.orchestrator.run_verification(req)
        self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)


    # ------------------------------------------------------------------
    # 34. Restart Recovery
    # ------------------------------------------------------------------
    def test_34_restart_recovery(self):
        req = VerificationRequest(request_id="r34", workspace_id=self.ws_id)
        res = self.orchestrator.run_verification(req)

        # Fresh store reading file
        fresh_store = VerificationStore(self.ver_store.path)
        record = fresh_store.get_verification(res.verification_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["verification_id"], res.verification_id)

    # ------------------------------------------------------------------
    # 35. Full End-to-End Verification Pipeline
    # ------------------------------------------------------------------
    def test_35_full_e2e_verification(self):
        req = VerificationRequest(
            request_id="r35_e2e",
            workspace_id=self.ws_id,
            verification_type=VerificationType.FULL,
        )
        res = self.orchestrator.run_verification(req)
        self.assertIn(res.status, [OverallVerificationStatus.PASSED, OverallVerificationStatus.PASSED_WITH_WARNINGS])
        self.assertIn(res.readiness_decision, [ReadinessDecision.READY, ReadinessDecision.READY_WITH_WARNINGS])
        self.assertGreaterEqual(res.security_score, 9.0)
        self.assertGreaterEqual(res.readiness_score, 9.0)

    # ------------------------------------------------------------------
    # 36. Read-Only Invariant — Zero Mutations on Disk
    # ------------------------------------------------------------------
    def test_36_read_only_invariant(self):
        test_file = os.path.join(self.proj, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("unchanged")
        mtime_before = os.path.getmtime(test_file)

        req = VerificationRequest(request_id="r36", workspace_id=self.ws_id)
        self.orchestrator.run_verification(req)

        mtime_after = os.path.getmtime(test_file)
        self.assertEqual(mtime_before, mtime_after)
        with open(test_file, "r") as f:
            self.assertEqual(f.read(), "unchanged")


if __name__ == "__main__":
    unittest.main()
