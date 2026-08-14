"""
Phase 2G — Central Authentication Service
Handles user registration, credential verification, rate-limited login, and token validation.
Enforces bounded memory for rate limiting and constant-time comparisons.
"""
from __future__ import annotations
import time
import uuid
import threading
from typing import Optional, Tuple, Dict, Any

from auth.store import AuthStore
from auth.password import PasswordManager
from auth.sessions import SessionManager
from auth.schemas import (
    User, UserInDB, Session, RegisterRequest, LoginRequest,
    UserRole, UserStatus
)
from auth.errors import (
    AuthError,
    INVALID_CREDENTIALS,
    USER_ALREADY_EXISTS,
    USER_DISABLED,
    RATE_LIMITED,
)
from auth.audit import log_auth_audit

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 minutes
MAX_RATE_LIMIT_TRACKED_USERS = 1000

_rate_limit_lock = threading.RLock()


class AuthenticationService:
    """Core service managing user authentication and security controls."""

    def __init__(self, store: Optional[AuthStore] = None):
        self._store = store or AuthStore()
        self._session_mgr = SessionManager(self._store)
        self._failed_attempts: Dict[str, Dict[str, Any]] = {}

    def register_user(self, req: RegisterRequest) -> User:
        """Registers a new user account."""
        start_t = time.perf_counter()
        norm_username = req.username.strip().lower()

        # Check existence
        existing = self._store.get_user_by_username(norm_username)
        if existing:
            raise AuthError(USER_ALREADY_EXISTS, f"Username '{req.username}' is already taken.")

        # Validate password strength
        valid_pw, reason = PasswordManager.validate_password_strength(req.password)
        if not valid_pw:
            raise AuthError(INVALID_CREDENTIALS, reason)

        user_id = f"usr_{uuid.uuid4().hex[:10]}"
        tenant_id = req.tenant_id or f"tnt_{uuid.uuid4().hex[:8]}"

        pw_hash, salt = PasswordManager.hash_password(req.password)

        user_db = UserInDB(
            user_id=user_id,
            tenant_id=tenant_id,
            username=req.username.strip(),
            email=req.email,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            password_hash=pw_hash,
            salt=salt,
        )

        self._store.save_user(user_db.model_dump())
        dur = (time.perf_counter() - start_t) * 1000

        log_auth_audit(
            request_id=f"reg_{user_id[:6]}",
            user_id=user_id,
            tenant_id=tenant_id,
            action="REGISTER",
            resource_type="USER",
            status="SUCCESS",
            duration_ms=dur,
        )

        return User(
            user_id=user_id,
            tenant_id=tenant_id,
            username=user_db.username,
            email=user_db.email,
            role=user_db.role,
            status=user_db.status,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at,
        )

    def authenticate(self, req: LoginRequest) -> Tuple[str, Session, User]:
        """
        Authenticates user credentials with rate limiting and constant-time checks.
        Returns: (raw_session_token, Session, User)
        """
        start_t = time.perf_counter()
        norm_username = req.username.strip().lower()

        # Check Rate Limit Lockout
        self._check_rate_limit(norm_username)

        user_data = self._store.get_user_by_username(norm_username)
        
        # If user not found, perform dummy hash to prevent timing attacks
        if not user_data:
            PasswordManager.verify_password(req.password, "00" * 32, "00" * 16)
            self._record_failed_attempt(norm_username)
            dur = (time.perf_counter() - start_t) * 1000
            log_auth_audit(
                request_id="login_fail",
                user_id="unknown",
                tenant_id="unknown",
                action="LOGIN",
                resource_type="SESSION",
                status="FAILED",
                duration_ms=dur,
                reason_code=INVALID_CREDENTIALS,
            )
            raise AuthError(INVALID_CREDENTIALS, "Invalid username or password.")

        user_db = UserInDB(**user_data)

        if user_db.status == UserStatus.DISABLED:
            raise AuthError(USER_DISABLED, "User account is disabled.")

        # Verify password
        is_valid = PasswordManager.verify_password(req.password, user_db.password_hash, user_db.salt)
        if not is_valid:
            self._record_failed_attempt(norm_username)
            dur = (time.perf_counter() - start_t) * 1000
            log_auth_audit(
                request_id=f"login_{user_db.user_id[:6]}",
                user_id=user_db.user_id,
                tenant_id=user_db.tenant_id,
                action="LOGIN",
                resource_type="SESSION",
                status="FAILED",
                duration_ms=dur,
                reason_code=INVALID_CREDENTIALS,
            )
            raise AuthError(INVALID_CREDENTIALS, "Invalid username or password.")

        # Clear failed attempts on successful login
        self._clear_failed_attempts(norm_username)

        # Create session
        session_id, raw_token, session = self._session_mgr.create_session(
            user_id=user_db.user_id,
            tenant_id=user_db.tenant_id,
        )

        user = User(
            user_id=user_db.user_id,
            tenant_id=user_db.tenant_id,
            username=user_db.username,
            email=user_db.email,
            role=user_db.role,
            status=user_db.status,
            created_at=user_db.created_at,
            updated_at=user_db.updated_at,
        )

        dur = (time.perf_counter() - start_t) * 1000
        log_auth_audit(
            request_id=f"login_{user_db.user_id[:6]}",
            user_id=user_db.user_id,
            tenant_id=user_db.tenant_id,
            action="LOGIN",
            resource_type="SESSION",
            status="SUCCESS",
            duration_ms=dur,
            session_id=session_id,
        )

        return raw_token, session, user

    # ------------------------------------------------------------------
    # Rate Limiting Helpers
    # ------------------------------------------------------------------

    def _check_rate_limit(self, username_norm: str):
        with _rate_limit_lock:
            record = self._failed_attempts.get(username_norm)
            if not record:
                return

            now = time.time()
            if now - record["first_failed_at"] > LOCKOUT_WINDOW_SECONDS:
                del self._failed_attempts[username_norm]
                return

            if record["count"] >= MAX_FAILED_ATTEMPTS:
                raise AuthError(RATE_LIMITED, "Too many failed login attempts. Please wait 5 minutes before trying again.")

    def _record_failed_attempt(self, username_norm: str):
        with _rate_limit_lock:
            now = time.time()
            if len(self._failed_attempts) > MAX_RATE_LIMIT_TRACKED_USERS:
                # Prune oldest
                oldest_keys = sorted(self._failed_attempts.keys(), key=lambda k: self._failed_attempts[k]["first_failed_at"])
                for k in oldest_keys[:100]:
                    del self._failed_attempts[k]

            if username_norm not in self._failed_attempts:
                self._failed_attempts[username_norm] = {"count": 1, "first_failed_at": now}
            else:
                self._failed_attempts[username_norm]["count"] += 1

    def _clear_failed_attempts(self, username_norm: str):
        with _rate_limit_lock:
            self._failed_attempts.pop(username_norm, None)
