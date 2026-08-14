"""
Phase 2G — Authentication Models & Enums
Exports domain structures and utility helpers for user identity and session management.
"""
from __future__ import annotations
from auth.schemas import (
    User, UserInDB, Session, AuthenticationContext,
    UserRole, UserStatus, RegisterRequest, LoginRequest,
    LoginResponse, SessionResponse
)

__all__ = [
    "User",
    "UserInDB",
    "Session",
    "AuthenticationContext",
    "UserRole",
    "UserStatus",
    "RegisterRequest",
    "LoginRequest",
    "LoginResponse",
    "SessionResponse",
]
