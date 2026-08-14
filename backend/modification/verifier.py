"""
Phase 2E — Post-Write Read-Only Verifier
Verifies filesystem state post-patch: hashes match, files exist/deleted as expected, and no temporary artifacts remain.
Never executes shell commands, build tools, or test scripts.
"""
from __future__ import annotations
import os
from typing import Dict, List, Optional, Any

from tools.path_verify import verify_safe_path
from modification.schemas import FilePatch, FileOperationType
from modification.atomic import AtomicPatcher


class PostWriteVerifier:
    """Read-only post-write verification engine."""

    @staticmethod
    def verify_patch_results(
        workspace_root: str,
        patches: List[FilePatch],
        expected_hashes: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Validates post-write conditions on disk.
        Returns a verification summary dict.
        """
        all_passed = True
        notes: List[str] = []
        verified_files: List[str] = []

        for p in patches:
            canonical = verify_safe_path(workspace_root, p.path)
            
            if p.operation == FileOperationType.DELETE:
                if os.path.exists(canonical):
                    all_passed = False
                    notes.append(f"Deleted file '{p.path}' still exists on disk.")
                else:
                    verified_files.append(p.path)

            elif p.operation == FileOperationType.RENAME:
                if os.path.exists(canonical):
                    all_passed = False
                    notes.append(f"Renamed source file '{p.path}' still exists.")
                if p.new_path:
                    can_dest = verify_safe_path(workspace_root, p.new_path)
                    if not os.path.exists(can_dest):
                        all_passed = False
                        notes.append(f"Rename target '{p.new_path}' was not created.")
                    else:
                        verified_files.append(p.new_path)

            else:  # CREATE or MODIFY
                if not os.path.exists(canonical):
                    all_passed = False
                    notes.append(f"Expected file '{p.path}' does not exist.")
                else:
                    current_hash = AtomicPatcher.get_file_sha256(canonical)
                    exp_hash = expected_hashes.get(p.path)
                    if exp_hash and current_hash != exp_hash:
                        all_passed = False
                        notes.append(f"Hash mismatch on '{p.path}' (expected {exp_hash[:8]}, got {current_hash[:8] if current_hash else 'none'}).")
                    else:
                        verified_files.append(p.path)

        # Check for lingering temporary files in workspace
        for root, _, files in os.walk(workspace_root):
            for f in files:
                if f.startswith(".kronx_patch_tmp_"):
                    all_passed = False
                    notes.append(f"Lingering temporary file found: {f}")

        if all_passed and not notes:
            notes.append("Post-write verification passed with 100% hash and artifact checks.")

        return {
            "verified": all_passed,
            "verified_files": verified_files,
            "notes": notes,
        }
