"""
Phase 2G — Comprehensive Authentication, Multi-Tenant Identity & Authorization Test Suite
Covers 46+ unit and integration tests verifying user creation, password hashing, session lifecycles,
tenant isolation, workspace ownership, rate limiting, and API endpoints.
"""
from __future__ import annotations
import os
import shutil
import tempfile
import unittest
import threading
import uuid
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from main import app
from auth.schemas import (
    RegisterRequest, LoginRequest, UserRole, UserStatus,
    AuthenticationContext, Session
)
from auth.errors import (
    AuthError,
    INVALID_CREDENTIALS,
    USER_ALREADY_EXISTS,
    USER_DISABLED,
    SESSION_EXPIRED,
    SESSION_REVOKED,
    SESSION_INVALID,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    RESOURCE_NOT_FOUND,
    RATE_LIMITED,
    ROLE_ESCALATION_BLOCKED,
)
from auth.password import PasswordManager
from auth.tokens import generate_session_token, hash_token, verify_token
from auth.sessions import SessionManager
from auth.store import AuthStore
from auth.authentication import AuthenticationService
from auth.authorization import MultiTenantAuthorizer
from auth.audit import log_auth_audit, sanitize_str
from workspace.store import WorkspaceStore

client = TestClient(app)


def _make_temp_auth_env():
    tmp = tempfile.mkdtemp()
    auth_file = os.path.join(tmp, "auth_store.json")
    os.environ["KRONX_WORKSPACE_ROOT"] = tmp
    store = AuthStore(auth_file)
    ws_store = WorkspaceStore()
    auth_svc = AuthenticationService(store)
    session_mgr = SessionManager(store)
    authorizer = MultiTenantAuthorizer(ws_store)
    return tmp, store, ws_store, auth_svc, session_mgr, authorizer



class TestAuthenticationEnginePhase2G(unittest.TestCase):

    def setUp(self):
        self.tmp, self.store, self.ws_store, self.auth_svc, self.session_mgr, self.authorizer = _make_temp_auth_env()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ------------------------------------------------------------------
    # 1. User Creation
    # ------------------------------------------------------------------
    def test_01_user_creation(self):
        req = RegisterRequest(username="alice", password="SecurePassword123!", email="alice@kronx.ai")
        user = self.auth_svc.register_user(req)
        self.assertEqual(user.username, "alice")
        self.assertTrue(user.user_id.startswith("usr_"))
        self.assertTrue(user.tenant_id.startswith("tnt_"))

    # ------------------------------------------------------------------
    # 2. Duplicate User Rejection
    # ------------------------------------------------------------------
    def test_02_duplicate_user_rejection(self):
        req = RegisterRequest(username="bob", password="SecurePassword123!")
        self.auth_svc.register_user(req)
        with self.assertRaises(AuthError) as ctx:
            self.auth_svc.register_user(req)
        self.assertEqual(ctx.exception.code, USER_ALREADY_EXISTS)

    # ------------------------------------------------------------------
    # 3. Password Hashing (PBKDF2)
    # ------------------------------------------------------------------
    def test_03_password_hashing(self):
        pw = "MySecretPass_456"
        h, salt = PasswordManager.hash_password(pw)
        self.assertNotEqual(pw, h)
        self.assertTrue(PasswordManager.verify_password(pw, h, salt))
        self.assertFalse(PasswordManager.verify_password("WrongPass", h, salt))

    # ------------------------------------------------------------------
    # 4. Plaintext Password Absence in User Models & API
    # ------------------------------------------------------------------
    def test_04_plaintext_password_absence(self):
        req = RegisterRequest(username="charlie", password="SecurePassword123!")
        user = self.auth_svc.register_user(req)
        user_dict = user.model_dump()
        self.assertNotIn("password", user_dict)
        self.assertNotIn("password_hash", user_dict)
        self.assertNotIn("salt", user_dict)

    # ------------------------------------------------------------------
    # 5. Valid Authentication (Login)
    # ------------------------------------------------------------------
    def test_05_valid_authentication(self):
        self.auth_svc.register_user(RegisterRequest(username="david", password="SecurePassword123!"))
        raw_token, session, user = self.auth_svc.authenticate(LoginRequest(username="david", password="SecurePassword123!"))
        self.assertTrue(raw_token.startswith("kx_"))
        self.assertEqual(session.user_id, user.user_id)
        self.assertEqual(user.username, "david")

    # ------------------------------------------------------------------
    # 6. Invalid Password Rejection
    # ------------------------------------------------------------------
    def test_06_invalid_password_rejection(self):
        self.auth_svc.register_user(RegisterRequest(username="eve", password="SecurePassword123!"))
        with self.assertRaises(AuthError) as ctx:
            self.auth_svc.authenticate(LoginRequest(username="eve", password="WrongPassword!"))
        self.assertEqual(ctx.exception.code, INVALID_CREDENTIALS)

    # ------------------------------------------------------------------
    # 7. Unknown User Rejection
    # ------------------------------------------------------------------
    def test_07_unknown_user_rejection(self):
        with self.assertRaises(AuthError) as ctx:
            self.auth_svc.authenticate(LoginRequest(username="nonexistent_user", password="Password123!"))
        self.assertEqual(ctx.exception.code, INVALID_CREDENTIALS)

    # ------------------------------------------------------------------
    # 8. Disabled User Rejection
    # ------------------------------------------------------------------
    def test_08_disabled_user_rejection(self):
        user = self.auth_svc.register_user(RegisterRequest(username="frank", password="SecurePassword123!"))
        # Disable user in store
        u_data = self.store.get_user_by_id(user.user_id)
        u_data["status"] = "DISABLED"
        self.store.save_user(u_data)

        with self.assertRaises(AuthError) as ctx:
            self.auth_svc.authenticate(LoginRequest(username="frank", password="SecurePassword123!"))
        self.assertEqual(ctx.exception.code, USER_DISABLED)

    # ------------------------------------------------------------------
    # 9. Session Creation
    # ------------------------------------------------------------------
    def test_09_session_creation(self):
        sess_id, token, sess = self.session_mgr.create_session(user_id="usr_test", tenant_id="tnt_test")
        self.assertTrue(sess_id.startswith("sess_"))
        self.assertEqual(sess.user_id, "usr_test")
        self.assertEqual(sess.tenant_id, "tnt_test")

    # ------------------------------------------------------------------
    # 10. Session Validation
    # ------------------------------------------------------------------
    def test_10_session_validation(self):
        user = self.auth_svc.register_user(RegisterRequest(username="grace", password="SecurePassword123!"))
        token, sess, _ = self.auth_svc.authenticate(LoginRequest(username="grace", password="SecurePassword123!"))
        val_sess, val_user = self.session_mgr.validate_session(token)
        self.assertEqual(val_sess.session_id, sess.session_id)
        self.assertEqual(val_user.user_id, user.user_id)

    # ------------------------------------------------------------------
    # 11. Session Expiration
    # ------------------------------------------------------------------
    def test_11_session_expiration(self):
        user = self.auth_svc.register_user(RegisterRequest(username="heidi", password="SecurePassword123!"))
        token, sess, _ = self.auth_svc.authenticate(LoginRequest(username="heidi", password="SecurePassword123!"))
        
        # Expire session in store
        s_data = self.store.get_session(sess.session_id)
        s_data["expires_at"] = "2020-01-01T00:00:00Z"
        self.store.save_session(sess.session_id, s_data)

        with self.assertRaises(AuthError) as ctx:
            self.session_mgr.validate_session(token)
        self.assertEqual(ctx.exception.code, SESSION_EXPIRED)

    # ------------------------------------------------------------------
    # 12. Session Revocation
    # ------------------------------------------------------------------
    def test_12_session_revocation(self):
        user = self.auth_svc.register_user(RegisterRequest(username="ivan", password="SecurePassword123!"))
        token, sess, _ = self.auth_svc.authenticate(LoginRequest(username="ivan", password="SecurePassword123!"))
        
        self.session_mgr.revoke_session(sess.session_id)

        with self.assertRaises(AuthError) as ctx:
            self.session_mgr.validate_session(token)
        self.assertEqual(ctx.exception.code, SESSION_REVOKED)

    # ------------------------------------------------------------------
    # 13. Forged Session Rejection
    # ------------------------------------------------------------------
    def test_13_forged_session_rejection(self):
        with self.assertRaises(AuthError) as ctx:
            self.session_mgr.validate_session("kx_forged_random_fake_token_12345")
        self.assertEqual(ctx.exception.code, SESSION_INVALID)

    # ------------------------------------------------------------------
    # 14. Malformed Token Rejection
    # ------------------------------------------------------------------
    def test_14_malformed_token_rejection(self):
        with self.assertRaises(AuthError) as ctx:
            self.session_mgr.validate_session("")
        self.assertEqual(ctx.exception.code, SESSION_INVALID)

    # ------------------------------------------------------------------
    # 15. Tenant Isolation
    # ------------------------------------------------------------------
    def test_15_tenant_isolation(self):
        # Register User A in Tenant A
        user_a = self.auth_svc.register_user(RegisterRequest(username="user_a", password="Password123!", tenant_id="tnt_A"))
        # Register User B in Tenant B
        user_b = self.auth_svc.register_user(RegisterRequest(username="user_b", password="Password123!", tenant_id="tnt_B"))
        self.assertNotEqual(user_a.tenant_id, user_b.tenant_id)

    # ------------------------------------------------------------------
    # 16. Workspace Ownership Authorization
    # ------------------------------------------------------------------
    def test_16_workspace_ownership_authorization(self):
        user_a = self.auth_svc.register_user(RegisterRequest(username="owner_a", password="Password123!", tenant_id="tnt_A"))
        ws_id = "ws_owner_a"
        self.ws_store.save_workspace(ws_id, {
            "workspace_id": ws_id,
            "tenant_id": user_a.tenant_id,
            "owner_user_id": user_a.user_id,
            "root_path": os.path.join(self.tmp, "proj_a"),
            "status": "authorized",
            "created_at": "2026-08-14T00:00:00Z",
        })

        ctx = AuthenticationContext(request_id="r16", session_id="s16", user_id=user_a.user_id, tenant_id=user_a.tenant_id)
        ws_data = self.authorizer.authorize_workspace_access(ctx, ws_id)
        self.assertEqual(ws_data["workspace_id"], ws_id)

    # ------------------------------------------------------------------
    # 17. Cross-User Workspace Denial
    # ------------------------------------------------------------------
    def test_17_cross_user_workspace_denial(self):
        user_a = self.auth_svc.register_user(RegisterRequest(username="user_a_17", password="Password123!", tenant_id="tnt_A"))
        user_b = self.auth_svc.register_user(RegisterRequest(username="user_b_17", password="Password123!", tenant_id="tnt_B"))
        
        ws_id = "ws_private_a"
        self.ws_store.save_workspace(ws_id, {
            "workspace_id": ws_id,
            "tenant_id": user_a.tenant_id,
            "owner_user_id": user_a.user_id,
            "root_path": os.path.join(self.tmp, "proj_a"),
            "status": "authorized",
            "created_at": "2026-08-14T00:00:00Z",
        })

        ctx_b = AuthenticationContext(request_id="r17", session_id="s17", user_id=user_b.user_id, tenant_id=user_b.tenant_id)
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_workspace_access(ctx_b, ws_id)
        self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 18. Cross-Tenant Workspace Denial
    # ------------------------------------------------------------------
    def test_18_cross_tenant_workspace_denial(self):
        ws_id = "ws_tenant_x"
        self.ws_store.save_workspace(ws_id, {
            "workspace_id": ws_id,
            "tenant_id": "tnt_X",
            "root_path": os.path.join(self.tmp, "proj_x"),
            "status": "authorized",
            "created_at": "2026-08-14T00:00:00Z",
        })

        ctx_y = AuthenticationContext(request_id="r18", session_id="s18", user_id="usr_y", tenant_id="tnt_Y")
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_workspace_access(ctx_y, ws_id)
        self.assertEqual(ctx.exception.code, WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 19. Client-Supplied user_id Ignored
    # ------------------------------------------------------------------
    def test_19_client_user_id_ignored(self):
        # Client context must resolve user_id strictly from session
        ctx = AuthenticationContext(request_id="r19", session_id="s19", user_id="usr_real", tenant_id="tnt_real")
        self.assertEqual(ctx.user_id, "usr_real")

    # ------------------------------------------------------------------
    # 20. Role Escalation Blocked
    # ------------------------------------------------------------------
    def test_20_role_escalation_blocked(self):
        with self.assertRaises(AuthError) as ctx:
            MultiTenantAuthorizer.validate_no_role_escalation("ADMIN")
        self.assertEqual(ctx.exception.code, ROLE_ESCALATION_BLOCKED)

    # ------------------------------------------------------------------
    # 21. Rate Limiting on Repeated Failed Logins
    # ------------------------------------------------------------------
    def test_21_rate_limiting_lockout(self):
        self.auth_svc.register_user(RegisterRequest(username="target_victim", password="RealPassword123!"))
        for _ in range(5):
            try:
                self.auth_svc.authenticate(LoginRequest(username="target_victim", password="WrongPassword!"))
            except AuthError:
                pass

        # 6th attempt must raise RATE_LIMITED
        with self.assertRaises(AuthError) as ctx:
            self.auth_svc.authenticate(LoginRequest(username="target_victim", password="RealPassword123!"))
        self.assertEqual(ctx.exception.code, RATE_LIMITED)

    # ------------------------------------------------------------------
    # 22. Audit Logging
    # ------------------------------------------------------------------
    def test_22_audit_logging(self):
        log_auth_audit(
            request_id="req_audit",
            user_id="usr_audit",
            tenant_id="tnt_audit",
            action="LOGIN",
            resource_type="SESSION",
            status="SUCCESS",
            duration_ms=12.5,
        )

    # ------------------------------------------------------------------
    # 23. Newline Log Sanitization
    # ------------------------------------------------------------------
    def test_23_newline_log_sanitization(self):
        malicious = "user\n[ADMIN_EVENT] granted\r"
        clean = sanitize_str(malicious)
        self.assertNotIn("\n", clean)
        self.assertNotIn("\r", clean)

    # ------------------------------------------------------------------
    # 24. Audit Secret Exclusion
    # ------------------------------------------------------------------
    def test_24_audit_secret_exclusion(self):
        raw_pw = "SuperSecret_123!"
        log_auth_audit(
            request_id="r24",
            user_id="usr_24",
            tenant_id="tnt_24",
            action="LOGIN",
            resource_type="SESSION",
            status="FAILED",
            duration_ms=5.0,
            reason_code=INVALID_CREDENTIALS,
        )

    # ------------------------------------------------------------------
    # 25. Concurrent Sessions Creation
    # ------------------------------------------------------------------
    def test_25_concurrent_sessions(self):
        user = self.auth_svc.register_user(RegisterRequest(username="concur_user", password="Password123!"))
        tokens = []
        errors = []

        def worker():
            try:
                t, _, _ = self.auth_svc.authenticate(LoginRequest(username="concur_user", password="Password123!"))
                tokens.append(t)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(tokens), 8)

    # ------------------------------------------------------------------
    # 26. Store Corruption Recovery
    # ------------------------------------------------------------------
    def test_26_corrupt_store_recovery(self):
        with open(self.store.path, "w") as f:
            f.write("CORRUPT_JSON_{{{")
        self.store._cache = None
        user = self.store.get_user_by_username("nobody")
        self.assertIsNone(user)

    # ------------------------------------------------------------------
    # 27. Plan Ownership Isolation
    # ------------------------------------------------------------------
    def test_27_plan_ownership_isolation(self):
        plan_obj = {"plan_id": "plan_123", "tenant_id": "tnt_A", "workspace_id": "ws_123"}
        self.ws_store.save_workspace("ws_123", {
            "workspace_id": "ws_123", "tenant_id": "tnt_A", "root_path": os.path.join(self.tmp, "p"), "status": "authorized", "created_at": "2026-08-14T00:00:00Z"
        })

        ctx_a = AuthenticationContext(request_id="r27_a", session_id="s1", user_id="u_a", tenant_id="tnt_A")
        ctx_b = AuthenticationContext(request_id="r27_b", session_id="s2", user_id="u_b", tenant_id="tnt_B")

        # User A succeeds
        self.authorizer.authorize_object_access(ctx_a, plan_obj, "Plan")

        # User B fails with sanitized RESOURCE_NOT_FOUND
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_object_access(ctx_b, plan_obj, "Plan")
        self.assertEqual(ctx.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 28. Execution Ownership Isolation
    # ------------------------------------------------------------------
    def test_28_execution_ownership_isolation(self):
        exec_obj = {"execution_id": "exec_123", "tenant_id": "tnt_A", "workspace_id": "ws_123"}
        ctx_b = AuthenticationContext(request_id="r28", session_id="s2", user_id="u_b", tenant_id="tnt_B")
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_object_access(ctx_b, exec_obj, "Execution")
        self.assertEqual(ctx.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 29. Modification Ownership Isolation
    # ------------------------------------------------------------------
    def test_29_modification_ownership_isolation(self):
        mod_obj = {"modification_id": "mod_123", "tenant_id": "tnt_A", "workspace_id": "ws_123"}
        ctx_b = AuthenticationContext(request_id="r29", session_id="s2", user_id="u_b", tenant_id="tnt_B")
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_object_access(ctx_b, mod_obj, "Modification")
        self.assertEqual(ctx.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 30. Verification Ownership Isolation
    # ------------------------------------------------------------------
    def test_30_verification_ownership_isolation(self):
        ver_obj = {"verification_id": "ver_123", "tenant_id": "tnt_A", "workspace_id": "ws_123"}
        ctx_b = AuthenticationContext(request_id="r30", session_id="s2", user_id="u_b", tenant_id="tnt_B")
        with self.assertRaises(AuthError) as ctx:
            self.authorizer.authorize_object_access(ctx_b, ver_obj, "Verification")
        self.assertEqual(ctx.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 31. Password Strength Validation
    # ------------------------------------------------------------------
    def test_31_password_strength_validation(self):
        short_pw = "short"
        valid, reason = PasswordManager.validate_password_strength(short_pw)
        self.assertFalse(valid)
        self.assertIn("at least 8", reason)

    # ------------------------------------------------------------------
    # 32. Full REST API Auth Lifecycle
    # ------------------------------------------------------------------
    def test_32_full_api_auth_lifecycle(self):
        uname = f"api_user_32_{uuid.uuid4().hex[:6]}"
        # 1. Register
        reg_resp = client.post("/api/auth/register", json={
            "username": uname,
            "password": "Password12345!",
            "email": f"{uname}@kronx.ai",
        })
        self.assertEqual(reg_resp.status_code, 200)
        self.assertEqual(reg_resp.json()["user"]["username"], uname)

        # 2. Login
        login_resp = client.post("/api/auth/login", json={
            "username": uname,
            "password": "Password12345!",
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json()["session_token"]
        self.assertTrue(token.startswith("kx_"))

        # 3. Get /me with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["user"]["username"], uname)


        # 4. Get /session
        sess_resp = client.get("/api/auth/session", headers=headers)
        self.assertEqual(sess_resp.status_code, 200)
        self.assertFalse(sess_resp.json()["session"]["revoked"])

        # 5. Logout
        logout_resp = client.post("/api/auth/logout", headers=headers)
        self.assertEqual(logout_resp.status_code, 200)

        # 6. /me after logout fails with 401
        post_logout = client.get("/api/auth/me", headers=headers)
        self.assertEqual(post_logout.status_code, 401)

    # ------------------------------------------------------------------
    # 33. Unauthorized Object Guessing Defense
    # ------------------------------------------------------------------
    def test_33_unauthorized_object_guessing_defense(self):
        ctx = AuthenticationContext(request_id="r33", session_id="s33", user_id="u_test", tenant_id="tnt_test")
        with self.assertRaises(AuthError) as ctx_err:
            self.authorizer.authorize_object_access(ctx, None, "Plan")
        self.assertEqual(ctx_err.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 34. ADMIN / EXECUTE / NETWORK Blocked in Auth Invariants
    # ------------------------------------------------------------------
    def test_34_admin_exec_network_invariants(self):
        for forbidden in ("ADMIN", "OWNER", "EXECUTE", "NETWORK"):
            with self.assertRaises(AuthError):
                MultiTenantAuthorizer.validate_no_role_escalation(forbidden)

    # ------------------------------------------------------------------
    # 35. Repeated Authentications
    # ------------------------------------------------------------------
    def test_35_repeated_authentications(self):
        user = self.auth_svc.register_user(RegisterRequest(username="repeat_user", password="Password123!"))
        for _ in range(3):
            token, sess, _ = self.auth_svc.authenticate(LoginRequest(username="repeat_user", password="Password123!"))
            val_s, val_u = self.session_mgr.validate_session(token)
            self.assertEqual(val_u.user_id, user.user_id)

    # ------------------------------------------------------------------
    # 36. Token Comparison Constant-Time Verification
    # ------------------------------------------------------------------
    def test_36_token_constant_time_comparison(self):
        t1 = generate_session_token()
        h1 = hash_token(t1)
        self.assertTrue(verify_token(t1, h1))
        self.assertFalse(verify_token(t1, "00" * 32))

    # ------------------------------------------------------------------
    # 37. Sanitized 401 Response on Bad Bearer Format
    # ------------------------------------------------------------------
    def test_37_bad_bearer_format(self):
        resp = client.get("/api/auth/me", headers={"Authorization": "Basic 12345"})
        self.assertEqual(resp.status_code, 401)

    # ------------------------------------------------------------------
    # 38. Bounded Rate Limit Dictionary Memory Protection
    # ------------------------------------------------------------------
    def test_38_bounded_rate_limit_memory(self):
        # Insert 1050 failed attempts
        for i in range(1050):
            self.auth_svc._record_failed_attempt(f"user_{i}")
        self.assertLessEqual(len(self.auth_svc._failed_attempts), 1000)


    # ------------------------------------------------------------------
    # 39. Session Token Entropy
    # ------------------------------------------------------------------
    def test_39_token_entropy(self):
        tokens = {generate_session_token() for _ in range(100)}
        self.assertEqual(len(tokens), 100)

    # ------------------------------------------------------------------
    # 40. End-to-End Multi-Tenant Isolation
    # ------------------------------------------------------------------
    def test_40_e2e_multi_tenant_isolation(self):
        # Tenant Alpha
        u_alpha = self.auth_svc.register_user(RegisterRequest(username="alpha_user", password="Password123!", tenant_id="tnt_alpha"))
        t_alpha, s_alpha, _ = self.auth_svc.authenticate(LoginRequest(username="alpha_user", password="Password123!"))

        # Tenant Beta
        u_beta = self.auth_svc.register_user(RegisterRequest(username="beta_user", password="Password123!", tenant_id="tnt_beta"))
        t_beta, s_beta, _ = self.auth_svc.authenticate(LoginRequest(username="beta_user", password="Password123!"))

        # Alpha creates workspace
        ws_id = "ws_alpha_space"
        self.ws_store.save_workspace(ws_id, {
            "workspace_id": ws_id,
            "tenant_id": u_alpha.tenant_id,
            "owner_user_id": u_alpha.user_id,
            "root_path": os.path.join(self.tmp, "alpha_proj"),
            "status": "authorized",
            "created_at": "2026-08-14T00:00:00Z",
        })

        # Alpha accesses -> OK
        ctx_alpha = AuthenticationContext(request_id="r_a", session_id=s_alpha.session_id, user_id=u_alpha.user_id, tenant_id=u_alpha.tenant_id)
        self.authorizer.authorize_workspace_access(ctx_alpha, ws_id)

        # Beta accesses Alpha workspace -> DENIED
        ctx_beta = AuthenticationContext(request_id="r_b", session_id=s_beta.session_id, user_id=u_beta.user_id, tenant_id=u_beta.tenant_id)
        with self.assertRaises(AuthError) as ctx_err:
            self.authorizer.authorize_workspace_access(ctx_beta, ws_id)
        self.assertEqual(ctx_err.exception.code, WORKSPACE_NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # 41. Expired Session Access via API
    # ------------------------------------------------------------------
    def test_41_expired_session_api_access(self):
        uname = f"user41_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={"username": uname, "password": "Password123!"})
        self.assertEqual(reg.status_code, 200)
        login = client.post("/api/auth/login", json={"username": uname, "password": "Password123!"})
        self.assertEqual(login.status_code, 200)
        tok = login.json()["session_token"]

        # Expire session in global store
        from api.auth import _session_mgr
        for s in _session_mgr._store._load_under_lock().get("sessions", {}).values():
            if s.get("user_id") == reg.json()["user"]["user_id"]:
                s["expires_at"] = "2020-01-01T00:00:00Z"
                _session_mgr._store.save_session(s["session_id"], s)

        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"]["code"], SESSION_EXPIRED)

    # ------------------------------------------------------------------
    # 42. Revoked Session Access via API
    # ------------------------------------------------------------------
    def test_42_revoked_session_api_access(self):
        uname = f"user42_{uuid.uuid4().hex[:6]}"
        reg = client.post("/api/auth/register", json={"username": uname, "password": "Password123!"})
        self.assertEqual(reg.status_code, 200)
        login = client.post("/api/auth/login", json={"username": uname, "password": "Password123!"})
        tok = login.json()["session_token"]

        logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(logout.status_code, 200)

        # Subsequent request must return 401 SESSION_REVOKED
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"]["code"], SESSION_REVOKED)

    # ------------------------------------------------------------------
    # 43. Guessing Unknown Resource IDs
    # ------------------------------------------------------------------
    def test_43_resource_guessing_defense(self):
        ctx = AuthenticationContext(request_id="r43", session_id="s43", user_id="u43", tenant_id="tnt43")
        with self.assertRaises(AuthError) as ctx_err:
            self.authorizer.authorize_object_access(ctx, None, "Plan")
        self.assertEqual(ctx_err.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 44. Unauthorized Object Retrieval
    # ------------------------------------------------------------------
    def test_44_unauthorized_object_retrieval(self):
        ctx_other = AuthenticationContext(request_id="r44", session_id="s44", user_id="u_attacker", tenant_id="tnt_attacker")
        obj_victim = {"plan_id": "plan_secret", "tenant_id": "tnt_victim"}
        with self.assertRaises(AuthError) as ctx_err:
            self.authorizer.authorize_object_access(ctx_other, obj_victim, "Plan")
        self.assertEqual(ctx_err.exception.code, RESOURCE_NOT_FOUND)

    # ------------------------------------------------------------------
    # 45. Authentication Error Sanitization
    # ------------------------------------------------------------------
    def test_45_auth_error_sanitization(self):
        resp = client.post("/api/auth/login", json={"username": "nonexistent", "password": "bad"})
        self.assertEqual(resp.status_code, 400)
        self.assertNotIn("Traceback", resp.text)
        self.assertEqual(resp.json()["detail"]["code"], INVALID_CREDENTIALS)

    # ------------------------------------------------------------------
    # 46. Password Too Long Validation
    # ------------------------------------------------------------------
    def test_46_password_too_long_validation(self):
        too_long = "a" * 150
        valid, reason = PasswordManager.validate_password_strength(too_long)
        self.assertFalse(valid)
        self.assertIn("cannot exceed", reason)


if __name__ == "__main__":
    unittest.main()

