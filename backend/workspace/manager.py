import os
import uuid
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Any

from workspace.store import WorkspaceStore
from workspace.scanner import WorkspaceScanner
from workspace.analyzer import ProjectAnalyzer
from workspace.schema import Workspace, ScanJob, ProjectProfile
from utils.logger import logger

# Bounded thread executor for scans (max 4 parallel scan threads)
_scan_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="kronx_scan_")
# Global map of cancellation events for running jobs
_cancellation_events: Dict[str, threading.Event] = {}
_jobs_lock = threading.Lock()

class WorkspaceManager:
    def __init__(self):
        self.store = WorkspaceStore()
        # Retrieve configured root boundary (insecure fallback disabled)
        self.root_boundary = os.getenv("KRONX_WORKSPACE_ROOT")
        if self.root_boundary:
            self.root_boundary = os.path.realpath(self.root_boundary)

    def _verify_within_root_boundary(self, path: str):
        """Verify that registered path lies inside KRONX_WORKSPACE_ROOT boundary."""
        if not self.root_boundary:
            # If root boundary is not configured, we allow registrations in development
            return
        
        real_path = os.path.realpath(path)
        try:
            common = os.path.commonpath([self.root_boundary, real_path])
            if common != self.root_boundary:
                raise ValueError("PATH_OUTSIDE_WORKSPACE")
        except Exception:
            raise ValueError("PATH_OUTSIDE_WORKSPACE")

    def register_workspace(self, root_path: str) -> Workspace:
        """Register and authorize a workspace root directory."""
        if not os.path.isdir(root_path):
            raise ValueError("INVALID_WORKSPACE")

        # 1. Enforce strict filesystem boundary
        self._verify_within_root_boundary(root_path)

        # 2. Path normalization
        resolved_path = os.path.realpath(root_path)

        # 3. Generate workspace ID from path hash or UUID
        workspace_id = f"ws_{uuid.uuid5(uuid.NAMESPACE_URL, resolved_path.replace('\\', '/')).hex[:8]}"

        existing = self.store.get_workspace(workspace_id)
        if existing:
            return Workspace(**existing)

        workspace_data = {
            "workspace_id": workspace_id,
            "root_path": resolved_path,
            "created_at": datetime.now().isoformat(),
            "status": "authorized"
        }
        self.store.save_workspace(workspace_id, workspace_data)
        logger.info(f"Registered workspace={workspace_id} path={resolved_path}")
        return Workspace(**workspace_data)

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        data = self.store.get_workspace(workspace_id)
        return Workspace(**data) if data else None

    def queue_scan(self, workspace_id: str) -> ScanJob:
        """Queue a non-blocking background workspace scan job."""
        ws = self.get_workspace(workspace_id)
        if not ws:
            raise ValueError("INVALID_WORKSPACE")

        job_id = f"scan_{uuid.uuid4().hex[:8]}"
        job_data = {
            "id": job_id,
            "workspace_id": workspace_id,
            "status": "QUEUED",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "progress": 0.0,
            "error": None,
            "result": None
        }
        self.store.save_job(job_id, job_data)
        
        # Initialize cooperative cancellation token
        cancel_event = threading.Event()
        with _jobs_lock:
            _cancellation_events[job_id] = cancel_event

        # Submit to bounded thread executor
        _scan_executor.submit(self._run_scan_job, job_id, ws.root_path, cancel_event)
        logger.info(f"Queued scan job={job_id} for workspace={workspace_id}")
        return ScanJob(**job_data)

    def get_job(self, job_id: str) -> Optional[ScanJob]:
        data = self.store.get_job(job_id)
        return ScanJob(**data) if data else None

    def cancel_job(self, job_id: str) -> ScanJob:
        """Request scan job cancellation and transition state cooperatively."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError("INVALID_JOB")

        with _jobs_lock:
            # 1. Trigger cooperative cancellation token event
            if job_id in _cancellation_events:
                _cancellation_events[job_id].set()
            
            # 2. State transition protection
            if job.status in ["QUEUED", "RUNNING"]:
                job_data = job.model_dump()
                job_data["status"] = "CANCELLED"
                job_data["completed_at"] = datetime.now().isoformat()
                self.store.save_job(job_id, job_data)
                logger.info(f"Cancelled scan job={job_id}")
                return ScanJob(**job_data)
            
        return job

    def _update_job_status(self, job_id: str, status: str, progress: float = 0.0, error: str = None, result: dict = None):
        """Update job status with strict state transition checks under lock."""
        with _jobs_lock:
            data = self.store.get_job(job_id)
            if not data:
                return

            current_status = data["status"]
            # Enforce valid state transition map
            # CANCELLED or COMPLETED or FAILED cannot transition further
            if current_status in ["COMPLETED", "FAILED", "CANCELLED"]:
                return

            data["status"] = status
            data["progress"] = progress
            if error:
                data["error"] = error
            if result:
                data["result"] = result
            if status in ["COMPLETED", "FAILED", "CANCELLED"]:
                data["completed_at"] = datetime.now().isoformat()
                # Clean up cancellation mapping
                if job_id in _cancellation_events:
                    del _cancellation_events[job_id]

            self.store.save_job(job_id, data)

    def _run_scan_job(self, job_id: str, root_path: str, cancel_event: threading.Event):
        """Core execution thread scan loop."""
        try:
            self._update_job_status(job_id, "RUNNING", progress=0.1)

            # Check cooperative cancellation before scan starts
            if cancel_event.is_set():
                self._update_job_status(job_id, "CANCELLED")
                return

            # 1. Run FS recursive read-only scan
            scanner = WorkspaceScanner()
            files, sensitive, stats = scanner.scan(root_path, cancellation_token=cancel_event)

            if cancel_event.is_set():
                self._update_job_status(job_id, "CANCELLED")
                return

            self._update_job_status(job_id, "RUNNING", progress=0.5)

            # 2. Run modular analysis and profiling
            analyzer = ProjectAnalyzer()
            profile = analyzer.analyze(root_path, files, sensitive, stats, cancellation_token=cancel_event)

            if cancel_event.is_set():
                self._update_job_status(job_id, "CANCELLED")
                return

            # 3. Transition to COMPLETED
            self._update_job_status(job_id, "COMPLETED", progress=1.0, result=profile.model_dump())
            logger.info(f"Completed scan job={job_id} successfully.")

        except ValueError as ve:
            if str(ve) == "SCAN_CANCELLED":
                self._update_job_status(job_id, "CANCELLED")
            else:
                self._update_job_status(job_id, "FAILED", error=str(ve))
        except Exception as e:
            logger.error(f"Scan job={job_id} failed: {e}", exc_info=True)
            self._update_job_status(job_id, "FAILED", error=str(e))
