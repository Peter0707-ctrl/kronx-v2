# Modification Package Init
from modification.orchestrator import ModificationOrchestrator
from modification.schemas import (
    ModificationRequest, ModificationProposal, AuthorizationRecord,
    ModificationResult, RollbackRecord, FilePatch, PatchPayload,
    ModificationMode, FileOperationType, ApprovalStatus, RollbackStatus,
)
from modification.errors import ModificationError

__all__ = [
    "ModificationOrchestrator",
    "ModificationRequest",
    "ModificationProposal",
    "AuthorizationRecord",
    "ModificationResult",
    "RollbackRecord",
    "FilePatch",
    "PatchPayload",
    "ModificationMode",
    "FileOperationType",
    "ApprovalStatus",
    "RollbackStatus",
    "ModificationError",
]
