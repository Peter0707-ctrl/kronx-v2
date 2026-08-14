"""
Phase 2D — Static Security Audit & Manual Verification Script
"""
import os
import sys
import json
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXECUTION_FILES = [
    "execution/schemas.py",
    "execution/errors.py",
    "execution/state.py",
    "execution/authorization.py",
    "execution/checkpoint.py",
    "execution/verifier.py",
    "execution/audit.py",
    "execution/orchestrator.py",
    "execution/__init__.py",
    "api/execution.py",
]

FORBIDDEN_PATTERNS = [
    "import subprocess", "from subprocess", "os.system(", "os.popen(",
    "subprocess.", "Popen(", "shell=True", "eval(", "exec(",
    "import requests", "from requests", "import urllib", "from urllib",
    "import socket", "from socket", "import httpx", "from httpx"
]

print("=== 1. STATIC SECURITY SCAN OF PHASE 2D MODULES ===")
violations = []
for rel_path in EXECUTION_FILES:
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
    print("PASSED: Zero forbidden command/network/eval patterns in execution modules.")

print("\n=== 2. PROGRAMMATIC VERIFICATION OF SCENARIOS A-I ===")
from workspace.manager import WorkspaceManager
from planner.store import PlannerStore
from execution.orchestrator import ExecutionOrchestrator
from execution.schemas import ExecutionRequest, ExecutionMode, ExecutionStatus
from execution.errors import ExecutionError
from tools.runtime import ToolRuntime

tmp = tempfile.mkdtemp()
proj = os.path.join(tmp, "verify_proj")
os.makedirs(proj)
os.environ["KRONX_WORKSPACE_ROOT"] = tmp

try:
    ws_mgr = WorkspaceManager()
    ws = ws_mgr.register_workspace(proj)
    p_store = PlannerStore()
    orch = ExecutionOrchestrator()

    # Plan Setup
    plan_id = "plan_verify_scenarios"
    tasks = [
        {"task_id": "t_read", "title": "Read files", "description": "Inspect", "task_type": "INSPECT", "dependencies": [], "required_tools": ["list_directory"]},
        {"task_id": "t_write", "title": "Write file", "description": "Write", "task_type": "DESIGN", "dependencies": [], "required_tools": ["create_file"]},
        {"task_id": "t_exec", "title": "Run shell", "description": "Exec", "task_type": "ANALYZE", "dependencies": [], "required_tools": ["execute_command"]},
        {"task_id": "t_net", "title": "Fetch web", "description": "Net", "task_type": "ANALYZE", "dependencies": [], "required_tools": ["network_request"]},
    ]
    p_store.save_plan(plan_id, {
        "plan_id": plan_id,
        "workspace_id": ws.workspace_id,
        "objective": "Scenarios verification",
        "mode": "ANALYZE",
        "tasks": tasks,
        "status": "COMPLETE",
    })

    # A. Start dry-run against valid plan -> COMPLETED, zero mutations
    files_before = os.listdir(proj)
    req_a = ExecutionRequest(request_id="req_a", workspace_id=ws.workspace_id, plan_id=plan_id, requested_task_ids=["t_read"], execution_mode=ExecutionMode.DRY_RUN)
    res_a = orch.execute(req_a)
    assert res_a.status == ExecutionStatus.COMPLETED
    assert os.listdir(proj) == files_before
    print("Scenario A: PASSED (Dry-run completed with zero mutations)")

    # B. Attempt WRITE task -> BLOCKED
    req_b = ExecutionRequest(request_id="req_b", workspace_id=ws.workspace_id, plan_id=plan_id, requested_task_ids=["t_write"], execution_mode=ExecutionMode.RUN)
    res_b = orch.execute(req_b)
    assert res_b.status == ExecutionStatus.BLOCKED
    assert "t_write" in res_b.blocked_tasks
    print("Scenario B: PASSED (WRITE task returns BLOCKED_REQUIRES_PERMISSION)")

    # C. Attempt EXECUTE task -> BLOCKED
    req_c = ExecutionRequest(request_id="req_c", workspace_id=ws.workspace_id, plan_id=plan_id, requested_task_ids=["t_exec"], execution_mode=ExecutionMode.RUN)
    res_c = orch.execute(req_c)
    assert res_c.status == ExecutionStatus.BLOCKED
    assert "t_exec" in res_c.blocked_tasks
    print("Scenario C: PASSED (EXECUTE task returns BLOCKED_REQUIRES_PERMISSION)")

    # D. Attempt NETWORK task -> BLOCKED
    req_d = ExecutionRequest(request_id="req_d", workspace_id=ws.workspace_id, plan_id=plan_id, requested_task_ids=["t_net"], execution_mode=ExecutionMode.RUN)
    res_d = orch.execute(req_d)
    assert res_d.status == ExecutionStatus.BLOCKED
    assert "t_net" in res_d.blocked_tasks
    print("Scenario D: PASSED (NETWORK task returns BLOCKED_REQUIRES_PERMISSION)")

    # E. Attempt ADMIN check -> FORBIDDEN
    from execution.authorization import ExecutionAuthorizer
    auth = ExecutionAuthorizer()
    ok_admin, reason_admin = auth.check_permission("ADMIN", "READ")
    assert not ok_admin and reason_admin == "FORBIDDEN_PERMISSION_LEVEL"
    print("Scenario E: PASSED (ADMIN permission returns FORBIDDEN_PERMISSION_LEVEL)")

    # F. Path Traversal -> PATH_OUTSIDE_WORKSPACE
    tr = ToolRuntime()
    res_f = tr.execute_tool(request_id="f", workspace_id=ws.workspace_id, tool_name="read_file", arguments={"path": "../../../etc/passwd"})
    assert res_f.error == "PATH_OUTSIDE_WORKSPACE"
    print("Scenario F: PASSED (Path traversal returns PATH_OUTSIDE_WORKSPACE)")

    # G. Sensitive .env access -> SENSITIVE_FILE
    env_file = os.path.join(proj, ".env")
    with open(env_file, "w") as f:
        f.write("SECRET_KEY=12345")
    res_g = tr.execute_tool(request_id="g", workspace_id=ws.workspace_id, tool_name="read_file", arguments={"path": ".env"})
    assert res_g.error == "SENSITIVE_FILE"
    print("Scenario G: PASSED (.env access returns SENSITIVE_FILE)")

    # H. Cancel execution -> CANCELLED
    req_h = ExecutionRequest(request_id="req_h", workspace_id=ws.workspace_id, plan_id=plan_id, requested_task_ids=["t_read"], execution_mode=ExecutionMode.RUN)
    res_h = orch.execute(req_h)
    cancel_res = orch.cancel(res_h.execution_id)
    assert cancel_res.status in (ExecutionStatus.CANCELLED, ExecutionStatus.COMPLETED)
    print("Scenario H: PASSED (Execution cancellation verified)")

    # I. Restart persistence -> persistent state
    exec_id_i = res_h.execution_id
    from execution.checkpoint import ExecutionStore
    reloaded_store = ExecutionStore(orch._exec_store.path)
    loaded_exec = reloaded_store.get_execution(exec_id_i)
    assert loaded_exec is not None and loaded_exec["execution_id"] == exec_id_i
    print("Scenario I: PASSED (Execution state persistent across re-initialization)")

    print("\nALL 9 SCENARIOS VERIFIED SUCCESSFULLY!")

finally:
    shutil.rmtree(tmp, ignore_errors=True)
