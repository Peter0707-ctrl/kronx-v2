"""
Phase 3.1 — Standardized Operational Errors & Exception Classes
"""
from typing import Optional, Dict, Any

# Lifecycle Error Codes
LIFECYCLE_INVALID_TRANSITION = "LIFECYCLE_INVALID_TRANSITION"
SYSTEM_NOT_READY             = "SYSTEM_NOT_READY"
SYSTEM_DRAINING              = "SYSTEM_DRAINING"
SYSTEM_STOPPED               = "SYSTEM_STOPPED"
UNAUTHORIZED_OPERATION       = "UNAUTHORIZED_OPERATION"

# Job Error Codes
JOB_NOT_FOUND                = "JOB_NOT_FOUND"
JOB_ALREADY_COMPLETED        = "JOB_ALREADY_COMPLETED"
JOB_CANCELLED                = "JOB_CANCELLED"
JOB_TIMEOUT                  = "JOB_TIMEOUT"

# Backup & Recovery Error Codes
BACKUP_FAILED                = "BACKUP_FAILED"
BACKUP_NOT_FOUND             = "BACKUP_NOT_FOUND"
BACKUP_CORRUPTED             = "BACKUP_CORRUPTED"
RECOVERY_BLOCKED             = "RECOVERY_BLOCKED"
RECOVERY_CONFLICT            = "RECOVERY_CONFLICT"
RECOVERY_FAILED              = "RECOVERY_FAILED"

# Store & Integrity Error Codes
STORE_CORRUPTED              = "STORE_CORRUPTED"
STORE_HASH_MISMATCH          = "STORE_HASH_MISMATCH"

# Incident & Config Error Codes
INCIDENT_NOT_FOUND           = "INCIDENT_NOT_FOUND"
CONFIG_INVALID               = "CONFIG_INVALID"
TENANT_MISMATCH              = "TENANT_MISMATCH"


class OperationsError(Exception):
    """Base exception for all operational subsystem errors."""
    def __init__(
        self,
        code: str,
        detail: str,
        status_code: int = 400,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        res = {"code": self.code, "message": self.detail}
        if self.extra:
            res["extra"] = self.extra
        return res
