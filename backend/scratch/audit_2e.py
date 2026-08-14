"""
Phase 2E — Static Security Audit & Manual Verification Script (Scenarios A through Q)
"""
import os
import sys
import json
import tempfile
import shutil
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODIFICATION_FILES = [
    "modification/schemas.py",
    "modification/errors.py",
    "modification/sensitive.py",
    "modification/diff_parser.py",
    "modification/stores.py",
    "modification/atomic.py",
    "modification/backup.py",
    "modification/validator.py",
    "modification/verifier.py",
    "modification/audit.py",
    "modification/orchestrator.py",
    "modification/__init__.py",
    "api/modification.py",
]

FORBIDDEN_PATTERNS = [
    "import subprocess", "from subprocess", "os.system(", "os.popen(",
    "subprocess.", "Popen(", "shell=True", "eval(", "exec(",
    "import requests", "from requests", "import urllib", "from urllib",
    "import socket", "from socket", "import httpx", "from httpx",
    "git ", "npm ", "pip ", "yarn "
]

print("=== 1. STATIC SECURITY SCAN OF PHASE 2E MODULES ===")
violations = []
for rel_path in MODIFICATION_FILES:
    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), rel_path)
    if not os.path.exists(full_path):
        violations.append(f"Missing file: {rel_path}")
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
    print("PASSED: Zero forbidden command/network/eval/shell patterns in modification modules.")

print("\n=== 2. PROGRAMMATIC VERIFICATION OF SCENARIOS A THROUGH Q ===")
from workspace.manager import WorkspaceManager
from modification.orchestrator import ModificationOrchestrator
from modification.schemas import (
    ModificationRequest, PatchPayload, FilePatch,
    FileOperationType, ModificationMode,
)
from modification.errors import ModificationError
from modification.atomic import compute_sha256
from tools.permissions import PermissionEngine

tmp = tempfile.mkdtemp()
proj = os.path.join(tmp, "verify_proj")
os.makedirs(proj)
os.environ["KRONX_WORKSPACE_ROOT"] = tmp

try:
    ws_mgr = WorkspaceManager()
    ws = ws_mgr.register_workspace(proj)
    orch = ModificationOrchestrator()

    # SCENARIO A: PROPOSE modification -> PROPOSED, 0 file mutation
    f_a = os.path.join(proj, "file_a.txt")
    patch_a = FilePatch(path="file_a.txt", operation=FileOperationType.CREATE, new_content="A content\n")
    prop_a = orch.propose(ModificationRequest(request_id="scen_a", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[patch_a])))
    assert prop_a.validation_status == "VALID"
    assert not os.path.exists(f_a)
    print("Scenario A: PASSED (PROPOSE creates proposal with zero disk mutations)")

    # SCENARIO B: PREVIEW modification -> VALID, 0 file mutation
    prev_b = orch.preview(prop_a.proposal_id)
    assert prev_b.validation_status == "VALID"
    assert not os.path.exists(f_a)
    print("Scenario B: PASSED (PREVIEW validates with zero disk mutations)")

    # SCENARIO C: Attempt APPLY without authorization -> BLOCKED_REQUIRES_PERMISSION
    try:
        orch.apply(prop_a.proposal_id, authorization_id="")
        assert False, "Should have raised ModificationError"
    except ModificationError as e:
        assert e.code == "BLOCKED_REQUIRES_PERMISSION"
    assert not os.path.exists(f_a)
    print("Scenario C: PASSED (APPLY without authorization blocked)")

    # SCENARIO D: Approve valid modification and APPLY -> APPLIED
    auth_d = orch.approve(prop_a.proposal_id)
    res_d = orch.apply(prop_a.proposal_id, auth_d.authorization_id)
    assert res_d.status == "APPLIED"
    assert os.path.exists(f_a)
    with open(f_a, "r") as f:
        assert f.read() == "A content\n"
    print("Scenario D: PASSED (Approved modification applied atomically and verified)")

    # SCENARIO E: Attempt .env modification -> SENSITIVE_FILE
    patch_e = FilePatch(path=".env", operation=FileOperationType.CREATE, new_content="DB_PASS=123")
    try:
        orch.propose(ModificationRequest(request_id="scen_e", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[patch_e])))
        assert False, "Should have raised SENSITIVE_FILE"
    except ModificationError as e:
        assert e.code == "SENSITIVE_FILE"
    print("Scenario E: PASSED (.env modification blocked as SENSITIVE_FILE)")

    # SCENARIO F: Attempt ../../../etc/passwd -> PATH_OUTSIDE_WORKSPACE
    patch_f = FilePatch(path="../../outside.txt", operation=FileOperationType.CREATE, new_content="out")
    try:
        orch.propose(ModificationRequest(request_id="scen_f", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[patch_f])))
        assert False, "Should have raised PATH_OUTSIDE_WORKSPACE"
    except ModificationError as e:
        assert e.code == "PATH_OUTSIDE_WORKSPACE"
    print("Scenario F: PASSED (Path traversal blocked as PATH_OUTSIDE_WORKSPACE)")

    # SCENARIO G: Attempt absolute outside path -> rejected
    from pydantic import ValidationError
    try:
        FilePatch(path="/etc/hosts", operation=FileOperationType.MODIFY)
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass
    print("Scenario G: PASSED (Absolute path rejected at schema validation)")

    # SCENARIO H: Modify file after proposal creation -> FILE_STATE_CHANGED
    f_h = os.path.join(proj, "file_h.txt")
    with open(f_h, "wb") as f: f.write(b"original_h")
    orig_h_hash = compute_sha256(b"original_h")
    patch_h = FilePatch(path="file_h.txt", operation=FileOperationType.MODIFY, expected_sha256=orig_h_hash, new_content="new_h")
    prop_h = orch.propose(ModificationRequest(request_id="scen_h", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[patch_h])))
    auth_h = orch.approve(prop_h.proposal_id)
    # External edit
    with open(f_h, "wb") as f: f.write(b"external_h")
    try:
        orch.apply(prop_h.proposal_id, auth_h.authorization_id)
        assert False, "Should have raised FILE_STATE_CHANGED"
    except ModificationError as e:
        assert e.code == "FILE_STATE_CHANGED"
    print("Scenario H: PASSED (Optimistic hash mismatch returns FILE_STATE_CHANGED without overwrite)")

    # SCENARIO I: Attempt WRITE self-escalation -> PERMISSION_DENIED / AUTHORIZATION_NOT_FOUND
    try:
        orch.apply(prop_a.proposal_id, authorization_id="fake_ai_token")
        assert False, "Should have failed authorization lookup"
    except ModificationError as e:
        assert e.code == "AUTHORIZATION_NOT_FOUND"
    print("Scenario I: PASSED (AI self-granted token rejected as AUTHORIZATION_NOT_FOUND)")

    # SCENARIO J: Attempt EXECUTE -> FORBIDDEN_PERMISSION_LEVEL
    pe = PermissionEngine()
    ok_j, r_j = pe.validate_permission("EXECUTE", "WRITE")
    assert not ok_j and r_j == "FORBIDDEN_PERMISSION_LEVEL"
    print("Scenario J: PASSED (EXECUTE permission is strictly FORBIDDEN_PERMISSION_LEVEL)")

    # SCENARIO K: Attempt NETWORK -> FORBIDDEN_PERMISSION_LEVEL
    ok_k, r_k = pe.validate_permission("NETWORK", "WRITE")
    assert not ok_k and r_k == "FORBIDDEN_PERMISSION_LEVEL"
    print("Scenario K: PASSED (NETWORK permission is strictly FORBIDDEN_PERMISSION_LEVEL)")

    # SCENARIO L: Attempt ADMIN -> FORBIDDEN_PERMISSION_LEVEL
    ok_l, r_l = pe.validate_permission("ADMIN", "WRITE")
    assert not ok_l and r_l == "FORBIDDEN_PERMISSION_LEVEL"
    print("Scenario L: PASSED (ADMIN permission is strictly FORBIDDEN_PERMISSION_LEVEL)")

    # SCENARIO M: Apply multi-file modification -> all-or-safe-failure
    patches_m = [
        FilePatch(path="multi_1.txt", operation=FileOperationType.CREATE, new_content="m1"),
        FilePatch(path="multi_2.txt", operation=FileOperationType.CREATE, new_content="m2"),
    ]
    prop_m = orch.propose(ModificationRequest(request_id="scen_m", workspace_id=ws.workspace_id, patch=PatchPayload(patches=patches_m)))
    auth_m = orch.approve(prop_m.proposal_id)
    res_m = orch.apply(prop_m.proposal_id, auth_m.authorization_id)
    assert res_m.status == "APPLIED"
    assert os.path.exists(os.path.join(proj, "multi_1.txt"))
    assert os.path.exists(os.path.join(proj, "multi_2.txt"))
    print("Scenario M: PASSED (Multi-file modification applied atomically)")

    # SCENARIO N: Rollback successful modification -> ROLLBACK_COMPLETED
    res_n = orch.rollback(res_m.modification_id)
    assert res_n.status == "ROLLBACK_COMPLETED"
    assert not os.path.exists(os.path.join(proj, "multi_1.txt"))
    assert not os.path.exists(os.path.join(proj, "multi_2.txt"))
    print("Scenario N: PASSED (Rollback restores pre-modification workspace state)")

    # SCENARIO O: Modify file after modification, then rollback -> ROLLBACK_CONFLICT
    patch_o = FilePatch(path="file_o.txt", operation=FileOperationType.CREATE, new_content="orig_o")
    prop_o = orch.propose(ModificationRequest(request_id="scen_o", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[patch_o])))
    auth_o = orch.approve(prop_o.proposal_id)
    res_o = orch.apply(prop_o.proposal_id, auth_o.authorization_id)
    # External edit post apply
    with open(os.path.join(proj, "file_o.txt"), "wb") as f: f.write(b"post_apply_edit")
    try:
        orch.rollback(res_o.modification_id)
        assert False, "Should have raised ROLLBACK_CONFLICT"
    except ModificationError as e:
        assert e.code == "ROLLBACK_CONFLICT"
    print("Scenario O: PASSED (Post-apply change detected, rollback aborted with ROLLBACK_CONFLICT)")

    # SCENARIO P: Restart application -> state remains persistent
    from modification.stores import ModificationStore
    new_store_p = ModificationStore(orch._mod_store.path)
    loaded_p = new_store_p.get_item(res_d.modification_id)
    assert loaded_p is not None and loaded_p["modification_id"] == res_d.modification_id
    print("Scenario P: PASSED (Modification state persistent across process re-initialization)")

    # SCENARIO Q: Concurrent modification requests -> no corruption, no partial writes
    errs_q = []
    def worker_q(idx):
        try:
            pq = FilePatch(path=f"cq_{idx}.txt", operation=FileOperationType.CREATE, new_content=f"cq_data_{idx}")
            prq = orch.propose(ModificationRequest(request_id=f"scen_q_{idx}", workspace_id=ws.workspace_id, patch=PatchPayload(patches=[pq])))
            aq = orch.approve(prq.proposal_id)
            rq = orch.apply(prq.proposal_id, aq.authorization_id)
            assert rq.status == "APPLIED"
        except Exception as e:
            errs_q.append(e)

    threads_q = [threading.Thread(target=worker_q, args=(i,)) for i in range(8)]
    for t in threads_q: t.start()
    for t in threads_q: t.join()
    assert len(errs_q) == 0
    print("Scenario Q: PASSED (8 concurrent modification operations executed without race or corruption)")

    print("\nALL 17 SCENARIOS (A THROUGH Q) VERIFIED SUCCESSFULLY!")

finally:
    shutil.rmtree(tmp, ignore_errors=True)
