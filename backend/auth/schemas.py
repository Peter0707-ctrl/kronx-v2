"""
Phase 2G — Authentication Schemas & Models
Strict Pydantic models for multi-tenant identity, sessions, and authorization context.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr, field_validator

# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------

class UserRole(str, Enum):
    USER  = "USER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    ACTIVE   = "ACTIVE"
    DISABLED = "DISABLED"


# ------------------------------------------------------------------
# User Models
# ------------------------------------------------------------------

class User(BaseModel):
    user_id:    str
    tenant_id:  str
    username:   str
    email:      Optional[str] = None
    role:       UserRole = UserRole.USER
    status:     UserStatus = UserStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    class Config:
        use_enum_values = True


class UserInDB(User):
    password_hash: str
    salt:          str


# ------------------------------------------------------------------
# Session Model
# ------------------------------------------------------------------

class Session(BaseModel):
    session_id:   str
    user_id:      str
    tenant_id:    str
    created_at:   str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    expires_at:   str
    revoked:      bool = False
    last_seen_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    token_hash:   str = ""

    class Config:
        use_enum_values = True


# ------------------------------------------------------------------
# Authentication Context
# ------------------------------------------------------------------

class AuthenticationContext(BaseModel):
    request_id: str
    session_id: str
    user_id:    str
    tenant_id:  str
    role:       UserRole = UserRole.USER

    class Config:
        use_enum_values = True


# ------------------------------------------------------------------
# API Request / Response Schemas
# ------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username:   str = Field(..., min_length=3, max_length=50)
    password:   str = Field(..., min_length=8, max_length=128)
    email:      Optional[str] = None
    tenant_id:  Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not v.isalnum() and "_" not in v and "-" not in v and "@" not in v and "." not in v:
            raise ValueError("Username can only contain alphanumeric characters, underscores, dashes, dots, or @.")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    status:        str = "ok"
    session_token: str
    expires_at:    str
    user:          User


class SessionResponse(BaseModel):
    status:  str = "ok"
    session: Session
    user:    User
