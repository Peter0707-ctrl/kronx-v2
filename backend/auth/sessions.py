"""
Phase 2G — Session Security & Management
Handles server-side session creation, validation, expiration, and revocation.
All operations are thread-safe and fail closed.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any

from auth.store import AuthStore
from auth.schemas import Session, User, UserStatus
from auth.tokens import generate_session_token, hash_token, verify_token
from auth.errors import (
    AuthError,
    SESSION_EXPIRED,
    SESSION_REVOKED,
    SESSION_INVALID,
    USER_DISABLED,
    USER_NOT_FOUND,
)

DEFAULT_SESSION_TTL_SECONDS = 3600  # 1 hour


class SessionManager:
    """Manages the lifecycle of user sessions."""

    def __init__(self, store: Optional[AuthStore] = None):
        self._store = store or AuthStore()

    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> Tuple[str, str, Session]:
        """
        Creates a new session for a user.
        Returns: (session_id, raw_token, session_object)
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        raw_token = generate_session_token()
        t_hash = hash_token(raw_token)

        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z")
        now_iso = now.isoformat().replace("+00:00", "Z")

        session = Session(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            created_at=now_iso,
            expires_at=expires_at,
            revoked=False,
            last_seen_at=now_iso,
            token_hash=t_hash,
        )

        self._store.save_session(session_id, session.model_dump())
        return session_id, raw_token, session

    def validate_session(self, raw_token: str) -> Tuple[Session, User]:
        """
        Validates a raw bearer session token and returns the associated session and user.
        Raises AuthError on any failure.
        """
        if not raw_token or not raw_token.strip():
            raise AuthError(SESSION_INVALID, "Missing or empty session token.")

        target_token_hash = hash_token(raw_token.strip())
        
        # Look up session by token hash
        sessions_dict = self._store._load_under_lock().get("sessions", {})
        matched_session_data = None

        for s_data in sessions_dict.values():
            if s_data.get("token_hash") and verify_token(raw_token.strip(), s_data["token_hash"]):
                matched_session_data = s_data
                break

        if not matched_session_data:
            raise AuthError(SESSION_INVALID, "Invalid or unrecognized session token.")

        session = Session(**matched_session_data)

        # Check Revocation
        if session.revoked:
            raise AuthError(SESSION_REVOKED, "This session has been revoked.")

        # Check Expiration
        try:
            expires_at_dt = datetime.fromisoformat(session.expires_at.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            if now_utc > expires_at_dt:
                raise AuthError(SESSION_EXPIRED, "This session has expired.")
        except AuthError:
            raise
        except Exception:
            raise AuthError(SESSION_INVALID, "Invalid session expiration timestamp.")

        # Check User State
        user_data = self._store.get_user_by_id(session.user_id)
        if not user_data:
            raise AuthError(USER_NOT_FOUND, "User associated with session not found.")

        user = User(**user_data)
        if user.status == UserStatus.DISABLED:
            raise AuthError(USER_DISABLED, "User account is disabled.")

        # Update last_seen_at
        session.last_seen_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._store.save_session(session.session_id, session.model_dump())

        return session, user

    def revoke_session(self, session_id: str):
        """Revokes a session immediately."""
        s_data = self._store.get_session(session_id)
        if s_data:
            s_data["revoked"] = True
            self._store.save_session(session_id, s_data)
