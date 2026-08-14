import unittest
import os
import sys
import json
import shutil
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock

# Adjust sys.path to run tests from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workspace.manager import WorkspaceManager
from workspace.scanner import WorkspaceScanner
from workspace.store import WorkspaceStore
from workspace.schema import ProjectProfile
from fastapi.testclient import TestClient
from main import app

class TestWorkspaceEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_root = os.path.join(self.test_dir, "test_proj")
        os.makedirs(self.workspace_root)
        
        # Configure env variables for testing boundaries
        self.original_boundary = os.environ.get("KRONX_WORKSPACE_ROOT")
        os.environ["KRONX_WORKSPACE_ROOT"] = self.test_dir

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if self.original_boundary:
            os.environ["KRONX_WORKSPACE_ROOT"] = self.original_boundary
        else:
            os.environ.pop("KRONX_WORKSPACE_ROOT", None)

    # ==========================================
    # 1. SECURITY & BOUNDARY TESTS
    # ==========================================
    def test_path_traversal_escapes(self):
        """Verify that target paths escaping the workspace root are blocked."""
        scanner = WorkspaceScanner()
        
        # Test escaping root using relative pathing
        with self.assertRaises(ValueError) as ctx:
            scanner.verify_safe_path(self.workspace_root, "../../etc/passwd")
        self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")
        
        # Test absolute pathing escape
        outside_path = os.path.dirname(self.test_dir)
        with self.assertRaises(ValueError) as ctx:
            scanner.verify_safe_path(self.workspace_root, outside_path)
        self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")

    def test_unauthorized_workspace_root_registration(self):
        """Verify registration fails if root lies outside KRONX_WORKSPACE_ROOT."""
        manager = WorkspaceManager()
        # Create a directory outside KRONX_WORKSPACE_ROOT
        outside_dir = tempfile.mkdtemp()
        try:
            with self.assertRaises(ValueError) as ctx:
                manager.register_workspace(outside_dir)
            self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")
        finally:
            shutil.rmtree(outside_dir)

    def test_symlink_escapes(self):
        """Verify symlinks targeting files outside the workspace are blocked."""
        scanner = WorkspaceScanner()
        
        # Create a file outside the workspace root
        secret_file = os.path.join(self.test_dir, "secret_outside.txt")
        with open(secret_file, "w") as f:
            f.write("confidential data")
            
        # Create a symlink inside pointing outside (supported on Windows only with developer privilege, mock if fails)
        symlink_path = os.path.join(self.workspace_root, "link_outside.txt")
        try:
            os.symlink(secret_file, symlink_path)
            
            # Check target verification throws error
            with self.assertRaises(ValueError) as ctx:
                scanner.verify_safe_path(self.workspace_root, "link_outside.txt")
            self.assertEqual(str(ctx.exception), "PATH_OUTSIDE_WORKSPACE")
        except OSError:
            # Fallback for systems/permissions where symlinks cannot be created
            pass

    # ==========================================
    # 2. SCANNER TESTS
    # ==========================================
    def test_recursive_scan_and_ignored_directories(self):
        """Verify scanner ignores standard config directories (node_modules, .git, etc.)."""
        # Create test structure
        os.makedirs(os.path.join(self.workspace_root, "src"))
        os.makedirs(os.path.join(self.workspace_root, "node_modules"))
        os.makedirs(os.path.join(self.workspace_root, ".git"))
        
        # Write files
        with open(os.path.join(self.workspace_root, "src/main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(self.workspace_root, "node_modules/index.js"), "w") as f:
            f.write("console.log('ignored')")
            
        scanner = WorkspaceScanner()
        files, sensitive, stats = scanner.scan(self.workspace_root)
        
        rel_paths = [f.path for f in files]
        self.assertIn("src/main.py", rel_paths)
        self.assertNotIn("node_modules/index.js", rel_paths)

    def test_large_and_binary_files(self):
        """Verify large files and binary files are classified correctly."""
        # Create a large file exceeding 5MB limit
        large_file = os.path.join(self.workspace_root, "large_file.zip")
        with open(large_file, "wb") as f:
            f.write(b"\0" * (6 * 1024 * 1024))
            
        scanner = WorkspaceScanner()
        files, sensitive, stats = scanner.scan(self.workspace_root)
        
        rel_paths = [f.path for f in files]
        # Large files exceeding limit are ignored by scanner list
        self.assertNotIn("large_file.zip", rel_paths)

    # ==========================================
    # 3. SENSITIVE DATA PROTECTION
    # ==========================================
    def test_sensitive_file_protection(self):
        """Verify sensitive credentials are listed as metadata but contents are never returned."""
        env_file = os.path.join(self.workspace_root, ".env")
        with open(env_file, "w") as f:
            f.write("DB_PASSWORD=super_secret_password_123")
            
        scanner = WorkspaceScanner()
        files, sensitive, stats = scanner.scan(self.workspace_root)
        
        # Verify .env is categorized in sensitive list
        self.assertTrue(len(sensitive) > 0)
        self.assertEqual(sensitive[0].path, ".env")
        self.assertEqual(sensitive[0].category, "sensitive")
        
        # Verify no content returned
        for item in files:
            self.assertNotEqual(item.path, ".env")
            
        # Verify fake secret never appears in profile mapping representation
        manager = WorkspaceManager()
        ws = manager.register_workspace(self.workspace_root)
        job = manager.queue_scan(ws.workspace_id)
        
        # Wait for scan job completion
        for _ in range(20):
            job_status = manager.get_job(job.id)
            if job_status.status in ["COMPLETED", "FAILED", "CANCELLED"]:
                break
            time.sleep(0.1)
            
        job_status = manager.get_job(job.id)
        self.assertEqual(job_status.status, "COMPLETED")
        
        # Check profile result contains no raw passwords
        profile = job_status.result
        profile_str = json.dumps(profile)
        self.assertNotIn("super_secret_password_123", profile_str)

    # ==========================================
    # 4. ECOSYSTEM DETECTION TESTS
    # ==========================================
    def test_python_fastapi_detector(self):
        """Test Python FastAPI framework detection, imports, and routes scanning."""
        with open(os.path.join(self.workspace_root, "main.py"), "w") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/api/users')\ndef get_users(): pass")
        with open(os.path.join(self.workspace_root, "requirements.txt"), "w") as f:
            f.write("fastapi==0.100.0\nuvicorn>=0.20.0")
            
        manager = WorkspaceManager()
        ws = manager.register_workspace(self.workspace_root)
        job = manager.queue_scan(ws.workspace_id)
        
        for _ in range(20):
            job_status = manager.get_job(job.id)
            if job_status.status == "COMPLETED":
                break
            time.sleep(0.1)
            
        profile = ProjectProfile(**manager.get_job(job.id).result)
        self.assertIn("Python", profile.languages)
        self.assertEqual(profile.frameworks[0]["name"], "FastAPI")
        self.assertEqual(profile.entry_points[0].path, "main.py")
        self.assertEqual(profile.routes[0].path, "/api/users")
        self.assertEqual(profile.routes[0].method, "GET")
        self.assertEqual(profile.dependencies[0].name, "fastapi")
        self.assertEqual(profile.dependencies[0].version, "0.100.0")

    def test_node_typescript_detector(self):
        """Test Node.js, TypeScript, Next.js, and package.json dependency extraction."""
        package_json = {
            "name": "node-project",
            "main": "dist/index.js",
            "dependencies": {
                "next": "^13.0.0",
                "react": "^18.2.0"
            },
            "devDependencies": {
                "typescript": "^5.0.0",
                "jest": "^29.0.0"
            }
        }
        with open(os.path.join(self.workspace_root, "package.json"), "w") as f:
            json.dump(package_json, f)
            
        manager = WorkspaceManager()
        ws = manager.register_workspace(self.workspace_root)
        job = manager.queue_scan(ws.workspace_id)
        
        for _ in range(20):
            job_status = manager.get_job(job.id)
            if job_status.status == "COMPLETED":
                break
            time.sleep(0.1)
            
        profile = ProjectProfile(**manager.get_job(job.id).result)
        fws = [f["name"] for f in profile.frameworks]
        self.assertIn("Next.js", fws)
        self.assertIn("React", fws)
        self.assertEqual(profile.entry_points[0].path, "dist/index.js")
        self.assertTrue(any(d.name == "next" for d in profile.dependencies))

    # ==========================================
    # 5. JOB STATE MACHINE TESTS
    # ==========================================
    def test_job_transitions_and_cancellation(self):
        """Verify ScanJob state transitions validation (QUEUED, RUNNING, CANCELLED)."""
        manager = WorkspaceManager()
        ws = manager.register_workspace(self.workspace_root)
        
        job = manager.queue_scan(ws.workspace_id)
        self.assertEqual(job.status, "QUEUED")
        
        # Cancel the job
        cancelled_job = manager.cancel_job(job.id)
        self.assertEqual(cancelled_job.status, "CANCELLED")
        
        # Verify invalid transitions are prevented
        manager._update_job_status(job.id, "RUNNING")
        job_after = manager.get_job(job.id)
        # Should stay CANCELLED because CANCELLED is terminal
        self.assertEqual(job_after.status, "CANCELLED")

    # ==========================================
    # 6. API CONTRACT TESTS
    # ==========================================
    def test_workspace_api_endpoints(self):
        """Test API endpoints /api/workspace, /api/workspace/scan, status, and cancel."""
        client = TestClient(app)
        
        # 1. Register workspace
        payload = {"root_path": self.workspace_root}
        resp = client.post("/api/workspace", json=payload)
        self.assertEqual(resp.status_code, 200)
        workspace_id = resp.json()["workspace_id"]
        
        # 2. Trigger scan
        resp = client.post("/api/workspace/scan", json={"workspace_id": workspace_id})
        self.assertEqual(resp.status_code, 200)
        scan_id = resp.json()["id"]
        
        # 3. Get status
        resp = client.get(f"/api/workspace/scan/{scan_id}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp.json()["status"], ["QUEUED", "RUNNING", "COMPLETED"])
        
        # 4. Cancel scan
        resp = client.post(f"/api/workspace/scan/{scan_id}/cancel")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "CANCELLED")

if __name__ == "__main__":
    unittest.main()
