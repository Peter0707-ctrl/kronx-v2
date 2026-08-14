"""
Phase 2E — Modification Schemas
Strict Pydantic models and resource limits for the Controlled Code Modification, Patch & Atomic Write Engine.
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------
# Enumerations
# ------------------------------------------------------------------

class ModificationMode(str, Enum):
    PROPOSE  = "PROPOSE"
    PREVIEW  = "PREVIEW"
    APPLY    = "APPLY"
    ROLLBACK = "ROLLBACK"

class FileOperationType(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    RENAME = "RENAME"

class ApprovalStatus(str, Enum):
    UNUSED   = "UNUSED"
    APPROVED = "APPROVED"
    CONSUMED = "CONSUMED"
    EXPIRED  = "EXPIRED"
    REVOKED  = "REVOKED"

class RollbackStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    APPLIED   = "APPLIED"
    CONFLICT  = "CONFLICT"
    REVOKED   = "REVOKED"

# ------------------------------------------------------------------
# Resource Limits
# ------------------------------------------------------------------
MAX_PATCH_SIZE_BYTES            = 1 * 1024 * 1024   # 1 MB
MAX_FILES_PER_PATCH             = 50
MAX_FILE_WRITE_BYTES            = 5 * 1024 * 1024   # 5 MB
MAX_TOTAL_WRITE_BYTES           = 25 * 1024 * 1024  # 25 MB
MAX_ADDITIONS                   = 10000
MAX_DELETIONS                   = 10000
WRITE_AUTHORIZATION_TTL_SECONDS = 300               # 5 minutes

# ------------------------------------------------------------------
# Patch Models
# ------------------------------------------------------------------

class FilePatch(BaseModel):
    path:             str
    operation:        FileOperationType = FileOperationType.MODIFY
    expected_sha256:  Optional[str] = None
    diff_content:     Optional[str] = None
    new_content:      Optional[str] = None
    new_path:         Optional[str] = None  # Used for RENAME
    encoding:         str = "utf-8"

    @field_validator("path")
    @classmethod
    def validate_relative_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("File path cannot be empty.")
        if v.startswith("/") or v.startswith("\\") or (len(v) > 1 and v[1] == ":"):
            raise ValueError("Absolute paths are strictly rejected. Paths must be workspace-relative.")
        return v.strip().replace("\\", "/")

    @field_validator("new_path")
    @classmethod
    def validate_relative_new_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("new_path cannot be empty.")
            if v.startswith("/") or v.startswith("\\") or (len(v) > 1 and v[1] == ":"):
                raise ValueError("Absolute paths are strictly rejected. Paths must be workspace-relative.")
            return v.strip().replace("\\", "/")
        return v


class PatchPayload(BaseModel):
    patches: List[FilePatch] = Field(default_factory=list)

    @field_validator("patches")
    @classmethod
    def validate_patch_count(cls, v: List[FilePatch]) -> List[FilePatch]:
        if not v:
            raise ValueError("Patch cannot be empty.")
        if len(v) > MAX_FILES_PER_PATCH:
            raise ValueError(f"Too many files in patch (max {MAX_FILES_PER_PATCH}).")
        return v

# ------------------------------------------------------------------
# Request Model
# ------------------------------------------------------------------

class ModificationRequest(BaseModel):
    request_id:        str
    workspace_id:      str
    plan_id:           Optional[str] = None
    execution_id:      Optional[str] = None
    task_id:           Optional[str] = None
    authorization_id:  Optional[str] = None
    mode:              ModificationMode = ModificationMode.PREVIEW
    patch:             PatchPayload
    user_id:           Optional[str] = None
    session_id:        Optional[str] = None
    tenant_id:         Optional[str] = None

# ------------------------------------------------------------------
# Proposal Model (Stages 1 & 2)
# ------------------------------------------------------------------

class ModificationProposal(BaseModel):
    proposal_id:         str
    workspace_id:        str
    plan_id:             Optional[str] = None
    execution_id:        Optional[str] = None
    task_id:             Optional[str] = None
    files_affected:      List[str] = Field(default_factory=list)
    patch:               PatchPayload
    additions:           int = 0
    deletions:           int = 0
    modifications:       int = 0
    risk_level:          str = "MEDIUM"
    required_permission: str = "WRITE"
    sensitive_files:     List[str] = Field(default_factory=list)
    validation_status:   str = "VALID"
    warnings:            List[str] = Field(default_factory=list)
    created_at:          str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    expires_at:          str = ""

    class Config:
        use_enum_values = True

# ------------------------------------------------------------------
# Authorization Record Model
# ------------------------------------------------------------------

class AuthorizationRecord(BaseModel):
    authorization_id:      str
    workspace_id:          str
    plan_id:               Optional[str] = None
    execution_id:          Optional[str] = None
    task_id:               Optional[str] = None
    proposal_id:           str
    authorized_permission: str = "WRITE"
    authorized_at:         str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    expires_at:            str
    status:                ApprovalStatus = ApprovalStatus.APPROVED
    user_id:               Optional[str] = None
    session_id:            Optional[str] = None
    tenant_id:             Optional[str] = None

    class Config:
        use_enum_values = True

# ------------------------------------------------------------------
# Rollback Record Model
# ------------------------------------------------------------------

class RollbackRecord(BaseModel):
    rollback_id:     str
    modification_id: str
    workspace_id:    str
    affected_files:  List[str] = Field(default_factory=list)
    previous_hashes: Dict[str, str] = Field(default_factory=dict)
    new_hashes:      Dict[str, str] = Field(default_factory=dict)
    backups:         Dict[str, Optional[str]] = Field(default_factory=dict)  # relative_path -> base64/content
    created_at:      str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    status:          RollbackStatus = RollbackStatus.AVAILABLE

    class Config:
        use_enum_values = True

# ------------------------------------------------------------------
# Modification Result Model
# ------------------------------------------------------------------

class ModificationResult(BaseModel):
    modification_id:    str
    proposal_id:        str
    workspace_id:       str
    status:             str  # APPLIED, FAILED, ROLLBACK_COMPLETED, ROLLBACK_FAILED
    files_changed:      List[str] = Field(default_factory=list)
    files_created:      List[str] = Field(default_factory=list)
    files_deleted:      List[str] = Field(default_factory=list)
    bytes_written:      int = 0
    verification:       Dict[str, Any] = Field(default_factory=dict)
    rollback_available: bool = False
    rollback_id:        Optional[str] = None
    error:              Optional[str] = None
    audit_reference:    str = ""
    created_at:         str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    class Config:
        use_enum_values = True
