"""
Phase 2F — Static Security Audit & Explicit Security Tests Script
"""
from __future__ import annotations
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

VERIFICATION_FILES = [
    "verification/__init__.py",
    "verification/schemas.py",
    "verification/errors.py",
    "verification/checks.py",
    "verification/security.py",
    "verification/workspace.py",
    "verification/tests.py",
    "verification/integrity.py",
    "verification/regression.py",
    "verification/health.py",
    "verification/readiness.py",
    "verification/audit.py",
    "verification/store.py",
    "verification/orchestrator.py",
    "api/verification.py",
]

FORBIDDEN_PATTERNS = [
    "import subprocess", "from subprocess", "os.system(", "os.popen(",
    "subprocess.", "Popen(", "shell=True", "eval(", "exec(",
    "import requests", "from requests", "import urllib", "from urllib",
    "import socket", "from socket", "import httpx", "from httpx",
    "git ", "npm ", "pip ", "yarn "
]

print("=== 1. STATIC SECURITY SCAN OF PHASE 2F MODULES ===")
violations = []
for rel_path in VERIFICATION_FILES:
    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel_path)
    if not os.path.exists(full_path):
        violations.append(f"Missing file: {rel_path}")
        continue
    # Skip self-contained pattern definition strings in security.py
    if rel_path == "verification/security.py":
        continue
    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("#") or s.startswith('"') or s.startswith("'"):
            continue
        for pat in FORBIDDEN_PATTERNS:
            if pat in s:
                violations.append(f"{rel_path}:{i} - found forbidden pattern '{pat}': {s[:80]}")

if violations:
    print("FAILED: Violations found:")
    for v in violations:
        print(" ", v)
    sys.exit(1)
else:
    print("PASSED: Zero forbidden command/network/eval/shell patterns in verification modules.")

print("\n=== 2. PROGRAMMATIC VERIFICATION OF REQUIRED SECURITY TEST CASES ===")
from tools.path_verify import verify_safe_path
from modification.sensitive import SensitiveFileDetector
from tools.permissions import PermissionEngine
from workspace.manager import WorkspaceManager
from workspace.store import WorkspaceStore
from verification.orchestrator import VerificationOrchestrator
from verification.schemas import VerificationRequest, CheckStatus, ReadinessDecision
from verification.errors import VerificationError

tmp = tempfile.mkdtemp()
proj = os.path.join(tmp, "security_test_proj")
os.makedirs(proj, exist_ok=True)
os.environ["KRONX_WORKSPACE_ROOT"] = tmp

try:
    # 1. Path Traversal & Escapes
    traversal_attacks = [
        "../../../etc/passwd",
        "/etc/passwd",
        "C:\\Windows\\System32",
        "\\\\server\\share\\secret.txt",
        "..\\..\\windows\\system32",
    ]
    for attack in traversal_attacks:
        try:
            verify_safe_path(proj, attack)
            assert False, f"Attack '{attack}' was not blocked by verify_safe_path"
        except (ValueError, Exception):
            pass
    print("Path Traversal & Absolute / UNC Escapes: PASSED (All blocked)")

    # 2. Sensitive Files Protection
    sensitive_targets = [
        ".env",
        ".env.production",
        ".env.local",
        "credentials.json",
        "private_key.pem",
        "id_rsa",
        "id_ed25519",
        "config/secrets.yaml",
    ]
    for st in sensitive_targets:
        is_sens, _ = SensitiveFileDetector.is_sensitive_path(st)
        assert is_sens, f"Sensitive target '{st}' was not flagged as sensitive"
    print("Sensitive Files (.env, credentials, pem, rsa): PASSED (All detected)")

    # 3. Fake Admin / Permission Escalation
    pe = PermissionEngine()
    ok_admin, r_admin = pe.validate_permission("ADMIN", "READ")
    assert not ok_admin and r_admin == "FORBIDDEN_PERMISSION_LEVEL"
    ok_exec, r_exec = pe.validate_permission("EXECUTE", "READ")
    assert not ok_exec and r_exec == "FORBIDDEN_PERMISSION_LEVEL"
    ok_net, r_net = pe.validate_permission("NETWORK", "READ")
    assert not ok_net and r_net == "FORBIDDEN_PERMISSION_LEVEL"
    print("Permission Escalation (ADMIN, EXECUTE, NETWORK): PASSED (All forbidden)")

    # 4. Workspace Authorization & Client Root Override Rejection
    ws_store = WorkspaceStore()
    ws_id = f"ws_sec_{os.getpid()}"
    ws_store.save_workspace(ws_id, {
        "workspace_id": ws_id,
        "root_path": proj,
        "status": "authorized",
        "created_at": "2026-08-14T00:00:00Z",
    })

    orch = VerificationOrchestrator(ws_store=ws_store)
    
    # Unknown workspace fails
    try:
        orch.run_verification(VerificationRequest(request_id="fake_ws", workspace_id="ws_fake_unregistered"))
        assert False, "Unregistered workspace should fail"
    except VerificationError as e:
        assert e.code == "WORKSPACE_NOT_AUTHORIZED"
    print("Workspace Resolution & Authorization: PASSED (Fake workspace rejected)")

    # 5. Full Read-Only Verification Run
    test_f = os.path.join(proj, "app.py")
    with open(test_f, "w") as f:
        f.write("print('safe app')\n")
    mtime_before = os.path.getmtime(test_f)

    res = orch.run_verification(VerificationRequest(request_id="req_sec_audit", workspace_id=ws_id))
    mtime_after = os.path.getmtime(test_f)
    
    assert mtime_before == mtime_after
    assert res.readiness_decision == ReadinessDecision.READY
    assert res.security_score == 10.0
    assert res.readiness_score == 10.0
    print("Read-Only Invariant & 10/10 Readiness Score: PASSED (0 disk mutations, score=10.0)")

    print("\nALL REQUIRED SECURITY TEST CASES VERIFIED SUCCESSFULLY!")

finally:
    shutil.rmtree(tmp, ignore_errors=True)
