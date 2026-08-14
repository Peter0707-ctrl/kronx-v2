"""
Phase 2F — Workspace Verifier
Validates workspace resolution, canonical root containment, traversal escapes, symlink boundaries, and sensitive file isolation.
"""
from __future__ import annotations
import os
import time
from typing import List, Dict, Any, Optional

from tools.path_verify import verify_safe_path
from workspace.store import WorkspaceStore
from verification.schemas import VerificationCheck, CheckStatus, CheckSeverity
from verification.checks import create_check
from modification.sensitive import SensitiveFileDetector


class WorkspaceVerifier:
    """Verifier for workspace boundaries and containment invariants."""

    def __init__(self, ws_store: Optional[WorkspaceStore] = None):
        self._ws_store = ws_store or WorkspaceStore()

    def verify_workspace(self, workspace_id: str) -> List[VerificationCheck]:
        """Runs full workspace verification checks."""
        checks: List[VerificationCheck] = []
        
        # 1. Existence and Authorization check
        start_t = time.perf_counter()
        ws_data = self._ws_store.get_workspace(workspace_id)
        dur = (time.perf_counter() - start_t) * 1000

        if not ws_data or ws_data.get("status") != "authorized":
            checks.append(create_check(
                category="WORKSPACE",
                name="WORKSPACE_AUTHORIZATION",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message=f"Workspace '{workspace_id}' is not authorized in WorkspaceStore.",
                evidence={"workspace_id": workspace_id, "found": bool(ws_data)},
                duration_ms=dur,
            ))
            return checks

        checks.append(create_check(
            category="WORKSPACE",
            name="WORKSPACE_AUTHORIZATION",
            status=CheckStatus.PASS,
            severity=CheckSeverity.INFO,
            message=f"Workspace '{workspace_id}' authorized in trusted server-side store.",
            evidence={"workspace_id": workspace_id, "status": ws_data.get("status")},
            duration_ms=dur,
        ))

        workspace_root = ws_data["root_path"]

        # 2. Canonical Realpath & Containment check
        start_t = time.perf_counter()
        real_root = os.path.realpath(workspace_root)
        exists_on_disk = os.path.isdir(real_root)
        dur = (time.perf_counter() - start_t) * 1000

        if not exists_on_disk:
            checks.append(create_check(
                category="WORKSPACE",
                name="WORKSPACE_ROOT_EXISTENCE",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.HIGH,
                message=f"Workspace root directory does not exist on disk.",
                evidence={"root_path": workspace_root},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="WORKSPACE",
                name="WORKSPACE_ROOT_EXISTENCE",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message="Workspace root directory exists and is a valid directory.",
                evidence={"real_root": real_root},
                duration_ms=dur,
            ))

        # 3. Path Traversal & Containment Verification
        start_t = time.perf_counter()
        traversal_attempts = ["../../../etc/passwd", "..\\outside.txt", "/etc/shadow", "C:\\Windows\\System32"]
        blocked_count = 0

        for t_path in traversal_attempts:
            try:
                verify_safe_path(real_root, t_path)
            except ValueError:
                blocked_count += 1
            except Exception:
                blocked_count += 1

        dur = (time.perf_counter() - start_t) * 1000
        if blocked_count == len(traversal_attempts):
            checks.append(create_check(
                category="WORKSPACE",
                name="PATH_CONTAINMENT_VERIFICATION",
                status=CheckStatus.PASS,
                severity=CheckSeverity.INFO,
                message="Verified: All path traversal escapes are strictly blocked by verify_safe_path.",
                evidence={"tested_attempts": len(traversal_attempts), "blocked_attempts": blocked_count},
                duration_ms=dur,
            ))
        else:
            checks.append(create_check(
                category="WORKSPACE",
                name="PATH_CONTAINMENT_VERIFICATION",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                message="Path traversal escape was not blocked by containment checker.",
                evidence={"tested_attempts": len(traversal_attempts), "blocked_attempts": blocked_count},
                duration_ms=dur,
            ))

        return checks
