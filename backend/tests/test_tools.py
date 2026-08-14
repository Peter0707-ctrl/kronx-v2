import unittest
import os
import sys
import json
import shutil
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock

# Adjust path to find backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registry import registry, ToolDescriptor
from tools.runtime import ToolRuntime
from tools.errors import (
    WORKSPACE_NOT_AUTHORIZED, PATH_OUTSIDE_WORKSPACE, 
    TOOL_NOT_REGISTERED, PERMISSION_DENIED, SENSITIVE_FILE, INVALID_ARGUMENTS
)
from tools.audit import AUDIT_LOG_FILE
from workspace.manager import WorkspaceManager
from fastapi.testclient import TestClient
from main import app

class TestToolRuntimeAndPermissions(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.test_dir, "test_proj")
        os.makedirs(self.workspace_root)
        
        # Configure allowed root environment
        self.original_boundary = os.environ.get("KRONX_WORKSPACE_ROOT")
        os.environ["KRONX_WORKSPACE_ROOT"] = self.test_dir
        
        # Register workspace
        self.manager = WorkspaceManager()
        self.ws = self.manager.register_workspace(self.workspace_root)
        self.workspace_id = self.ws.workspace_id
        
        self.runtime = ToolRuntime()
        
        # Write dummy files to workspace
        with open(os.path.join(self.workspace_root, "safe.txt"), "w") as f:
            f.write("safe text content inside project")
            
        with open(os.path.join(self.workspace_root, ".env"), "w") as f:
            f.write("API_KEY=leak_this_super_secret_value_123")
            
        # Create a dummy binary file
        with open(os.path.join(self.workspace_root, "dummy.bin"), "wb") as f:
            f.write(b"\0\1\2\3hello binary content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if self.original_boundary:
            os.environ["KRONX_WORKSPACE_ROOT"] = self.original_boundary
        else:
            os.environ.pop("KRONX_WORKSPACE_ROOT", None)

    # ==========================================
    # 1. TOOL REGISTRY TESTS
    # ==========================================
    def test_registered_tool_executes(self):
        """Verify registered tool executes correctly."""
        res = self.runtime.execute_tool(
            request_id="req_1",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": "safe.txt"}
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data["content"], "safe text content inside project")

    def test_unknown_tool_denied(self):
        """Verify unknown tool returns TOOL_NOT_REGISTERED."""
        res = self.runtime.execute_tool(
            request_id="req_2",
            workspace_id=self.workspace_id,
            tool_name="unknown_tool_name",
            arguments={}
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error, TOOL_NOT_REGISTERED)

    # ==========================================
    # 2. PERMISSIONS TESTS
    # ==========================================
    def test_read_allowed_write_denied(self):
        """Verify default READ works and WRITE fails with PERMISSION_DENIED."""
        # 1. READ is allowed
        res_read = self.runtime.execute_tool(
            request_id="req_3",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": "safe.txt"},
            client_effective_permission="READ"
        )
        self.assertTrue(res_read.success)

        # 2. WRITE tools (create_file) are registered but raise PERMISSION_DENIED in 2B
        res_write = self.runtime.execute_tool(
            request_id="req_4",
            workspace_id=self.workspace_id,
            tool_name="create_file",
            arguments={"path": "new_file.txt", "content": "text"},
            client_effective_permission="WRITE"
        )
        self.assertFalse(res_write.success)
        self.assertEqual(res_write.error, PERMISSION_DENIED)

    def test_model_cannot_self_elevate(self):
        """Verify model requesting WRITE permission level gets blocked if not authorized."""
        # If the model requests execute_tool for create_file without authorization, it should return PERMISSION_DENIED
        res = self.runtime.execute_tool(
            request_id="req_5",
            workspace_id=self.workspace_id,
            tool_name="create_file",
            arguments={"path": "new_file.txt"},
            client_effective_permission="READ"  # requests lower than required
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error, PERMISSION_DENIED)

    # ==========================================
    # 3. WORKSPACE PATH SECURITY TESTS
    # ==========================================
    def test_traversal_denied(self):
        """Verify path traversal outside workspace returns PATH_OUTSIDE_WORKSPACE."""
        res = self.runtime.execute_tool(
            request_id="req_6",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": "../../outside_secret.txt"}
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error, PATH_OUTSIDE_WORKSPACE)

    def test_absolute_path_escape_denied(self):
        """Verify absolute paths outside workspace are blocked."""
        outside_abs = os.path.dirname(self.test_dir)
        res = self.runtime.execute_tool(
            request_id="req_7",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": outside_abs}
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error, PATH_OUTSIDE_WORKSPACE)

    def test_symlink_escape_denied(self):
        """Verify symlink targeting outside files returns PATH_OUTSIDE_WORKSPACE."""
        outside_file = os.path.join(self.test_dir, "outside.txt")
        with open(outside_file, "w") as f:
            f.write("secret data")
            
        symlink_path = os.path.join(self.workspace_root, "link_outside.txt")
        try:
            os.symlink(outside_file, symlink_path)
            res = self.runtime.execute_tool(
                request_id="req_8",
                workspace_id=self.workspace_id,
                tool_name="read_file",
                arguments={"path": "link_outside.txt"}
            )
            self.assertFalse(res.success)
            self.assertEqual(res.error, PATH_OUTSIDE_WORKSPACE)
        except OSError:
            # Fallback for systems without symlink creation privilege
            pass

    # ==========================================
    # 4. READ_FILE TESTS
    # ==========================================
    def test_read_file_sensitive(self):
        """Verify .env or credentials returns SENSITIVE_FILE."""
        res = self.runtime.execute_tool(
            request_id="req_9",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": ".env"}
        )
        self.assertFalse(res.success)
        self.assertEqual(res.error, SENSITIVE_FILE)

    def test_read_file_binary(self):
        """Verify binary file does not leak bytes and returns blocked notice."""
        res = self.runtime.execute_tool(
            request_id="req_10",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": "dummy.bin"}
        )
        self.assertTrue(res.success)
        self.assertEqual(res.data["content"], "[Binary Content Blocked]")
        self.assertTrue(res.data["binary"])

    # ==========================================
    # 5. LIST_DIRECTORY TESTS
    # ==========================================
    def test_list_directory_filters_sensitive(self):
        """Verify list_directory hides absolute paths and flags sensitive files."""
        res = self.runtime.execute_tool(
            request_id="req_11",
            workspace_id=self.workspace_id,
            tool_name="list_directory",
            arguments={"path": ""}
        )
        self.assertTrue(res.success)
        entries = res.data["entries"]
        
        # Verify relative paths only
        for entry in entries:
            self.assertFalse(os.path.isabs(entry["path"]))
            if entry["name"] == ".env":
                self.assertTrue(entry["sensitive"])
                # size should be zero to hide secrets
                self.assertEqual(entry["size"], 0)

    # ==========================================
    # 6. SEARCH_CODE TESTS
    # ==========================================
    def test_search_code_ignores_sensitive(self):
        """Verify search_code excludes sensitive files and query constraints."""
        res = self.runtime.execute_tool(
            request_id="req_12",
            workspace_id=self.workspace_id,
            tool_name="search_code",
            arguments={"query": "leak_this"}
        )
        self.assertTrue(res.success)
        # Should not find matches inside .env
        self.assertEqual(len(res.data["matches"]), 0)

    # ==========================================
    # 7. INSPECT_FILE TESTS
    # ==========================================
    def test_inspect_sensitive_and_binary(self):
        """Verify inspect_file returns metadata but no content."""
        # 1. Sensitive file inspection
        res_sens = self.runtime.execute_tool(
            request_id="req_13",
            workspace_id=self.workspace_id,
            tool_name="inspect_file",
            arguments={"path": ".env"}
        )
        self.assertTrue(res_sens.success)
        self.assertTrue(res_sens.data["sensitive"])
        self.assertEqual(res_sens.data["category"], "sensitive")

        # 2. Binary file inspection
        res_bin = self.runtime.execute_tool(
            request_id="req_14",
            workspace_id=self.workspace_id,
            tool_name="inspect_file",
            arguments={"path": "dummy.bin"}
        )
        self.assertTrue(res_bin.success)
        self.assertTrue(res_bin.data["binary"])

    # ==========================================
    # 8. AUDIT LOGGING TESTS
    # ==========================================
    def test_audit_logs_decisions_and_paths(self):
        """Verify tool calls log events into AUDIT_LOG_FILE without secrets or newlines."""
        # Force a DENY event
        self.runtime.execute_tool(
            request_id="req_audit_test\nfakeinjection",
            workspace_id=self.workspace_id,
            tool_name="read_file",
            arguments={"path": "../../passwd"}
        )
        
        # Verify log entry
        self.assertTrue(os.path.exists(AUDIT_LOG_FILE))
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            log_content = f.read()
            
        # Verify no newline injection occurred in request_id
        self.assertIn("req_audit_test fakeinjection", log_content)
        self.assertNotIn("req_audit_test\nfakeinjection", log_content)

    # ==========================================
    # 9. CONCURRENCY TESTS
    # ==========================================
    def test_concurrent_tool_execution(self):
        """Verify multiple threads reading and searching do not cause race conditions."""
        exceptions = []
        
        def reader_worker():
            try:
                for _ in range(10):
                    res = self.runtime.execute_tool(
                        request_id="req_concur",
                        workspace_id=self.workspace_id,
                        tool_name="read_file",
                        arguments={"path": "safe.txt"}
                    )
                    self.assertTrue(res.success)
            except Exception as e:
                exceptions.append(e)

        threads = [threading.Thread(target=reader_worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        self.assertEqual(len(exceptions), 0)

    # ==========================================
    # 10. ADVERSARIAL ATTACKS TESTS
    # ==========================================
    def test_adversarial_paths_and_permissions(self):
        """Test endpoint validation blocks traversal, Windows escaping, and injections."""
        client = TestClient(app)
        
        # 1. Traversal injection
        resp = client.post("/api/tools/execute", json={
            "workspace_id": self.workspace_id,
            "tool_name": "read_file",
            "arguments": {"path": "../../etc/passwd"}
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["detail"], PATH_OUTSIDE_WORKSPACE)

        # 2. Windows paths escape
        resp = client.post("/api/tools/execute", json={
            "workspace_id": self.workspace_id,
            "tool_name": "read_file",
            "arguments": {"path": "C:\\Windows\\System32\\cmd.exe"}
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["detail"], PATH_OUTSIDE_WORKSPACE)

        # 3. Forged permission request
        resp = client.post("/api/tools/execute", json={
            "workspace_id": self.workspace_id,
            "tool_name": "create_file",
            "arguments": {"path": "new_file.txt"},
            "effective_permission": "ADMIN" # try self-elevation
        })
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()["detail"], PERMISSION_DENIED)

if __name__ == "__main__":
    unittest.main()
