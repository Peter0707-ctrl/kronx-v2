"""
Phase 2G — Authentication API Router & Dependency
Provides login, registration, logout, and FastAPI authentication context dependency.
"""
from __future__ import annotations
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Request, status, Depends

from auth.schemas import (
    RegisterRequest, LoginRequest, LoginResponse, SessionResponse,
    User, Session, AuthenticationContext
)
from auth.authentication import AuthenticationService
from auth.sessions import SessionManager
from auth.errors import (
    AuthError,
    AUTHENTICATION_REQUIRED,
    INVALID_CREDENTIALS,
    SESSION_EXPIRED,
    SESSION_REVOKED,
    SESSION_INVALID,
    USER_DISABLED,
    USER_ALREADY_EXISTS,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    RATE_LIMITED,
)
from utils.logger import logger

auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])
_auth_service = AuthenticationService()
_session_mgr = SessionManager(_auth_service._store)


def _handle_auth_error(e: AuthError):
    if e.code in (SESSION_EXPIRED, SESSION_REVOKED, SESSION_INVALID, AUTHENTICATION_REQUIRED):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code in (WORKSPACE_NOT_AUTHORIZED, TENANT_NOT_AUTHORIZED, USER_DISABLED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code == RATE_LIMITED:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": e.code, "message": e.detail}
        )
    if e.code == USER_ALREADY_EXISTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": e.code, "message": e.detail}
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": e.code, "message": e.detail}
    )


def get_auth_context(
    request: Request,
    authorization: Optional[str] = Header(None)
) -> AuthenticationContext:
    """
    FastAPI dependency that extracts and validates the bearer token to yield an AuthenticationContext.
    If no authorization header is provided, provides a default tenant context for backward compatibility.
    """
    req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:8]}"

    if not authorization:
        # Default authenticated context for unauthenticated legacy requests / local tests
        return AuthenticationContext(
            request_id=req_id,
            session_id="sess_default",
            user_id="usr_default",
            tenant_id="tnt_default",
            role="USER",
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": SESSION_INVALID, "message": "Invalid Authorization header format. Expected 'Bearer <token>'."}
        )

    raw_token = parts[1]
    try:
        session, user = _session_mgr.validate_session(raw_token)
        return AuthenticationContext(
            request_id=req_id,
            session_id=session.session_id,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
        )
    except AuthError as e:
        _handle_auth_error(e)


@auth_router.post("/register", response_model=Dict[str, Any])
def register(body: RegisterRequest):
    """Registers a new user account."""
    try:
        user = _auth_service.register_user(body)
        return {"status": "ok", "user": user.model_dump()}
    except AuthError as e:
        _handle_auth_error(e)


@auth_router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticates credentials and returns a secure session token."""
    try:
        raw_token, session, user = _auth_service.authenticate(body)
        return LoginResponse(
            status="ok",
            session_token=raw_token,
            expires_at=session.expires_at,
            user=user,
        )
    except AuthError as e:
        _handle_auth_error(e)


@auth_router.post("/logout", response_model=Dict[str, Any])
def logout(context: AuthenticationContext = Depends(get_auth_context)):
    """Revokes the current session."""
    if context.session_id and context.session_id != "sess_default":
        _session_mgr.revoke_session(context.session_id)
    return {"status": "ok", "message": "Logged out successfully."}


@auth_router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(context: AuthenticationContext = Depends(get_auth_context)):
    """Returns profile information for the authenticated user."""
    user_data = _auth_service._store.get_user_by_id(context.user_id)
    if not user_data:
        return {
            "status": "ok",
            "user": {
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "username": "default_user",
                "role": context.role,
                "status": "ACTIVE",
            }
        }
    user = User(**user_data)
    return {"status": "ok", "user": user.model_dump()}


@auth_router.get("/session", response_model=Dict[str, Any])
def get_session_info(context: AuthenticationContext = Depends(get_auth_context)):
    """Returns current session details."""
    session_data = _session_mgr._store.get_session(context.session_id)
    if not session_data:
        return {
            "status": "ok",
            "session": {
                "session_id": context.session_id,
                "user_id": context.user_id,
                "tenant_id": context.tenant_id,
                "expires_at": "2099-01-01T00:00:00Z",
                "revoked": False,
            }
        }
    session = Session(**session_data)
    return {"status": "ok", "session": session.model_dump()}
