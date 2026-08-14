"""
Phase 3.1 — Job Lifecycle Engine
Tracks long-running agent, execution, modification, multimodal, and LLM jobs with cooperative cancellation.
Strict tenant isolation and bounded persistence.
"""
import uuid
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from operations.schemas import JobRecord, JobStatus
from operations.errors import OperationsError, JOB_NOT_FOUND, JOB_ALREADY_COMPLETED
from operations.store import OperationsStore
from operations.audit import log_operations_audit
from llm.sanitizer import sanitize_secrets

_jobs_lock = threading.RLock()


class JobLifecycleManager:
    def __init__(self, store: Optional[OperationsStore] = None):
        self._store = store or OperationsStore()

    def create_job(
        self,
        tenant_id: str,
        job_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> JobRecord:
        """Initializes a new job record with QUEUED status."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                clean_meta[k] = sanitize_secrets(v) if isinstance(v, str) else v

        job = JobRecord(
            job_id=job_id,
            tenant_id=tenant_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            progress=0.0,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            metadata=clean_meta,
        )

        with _jobs_lock:
            self._store.save_job(tenant_id, job_id, job.model_dump())

        log_operations_audit(
            action="JOB_CREATED",
            status="QUEUED",
            tenant_id=tenant_id,
            details={"job_id": job_id, "job_type": job_type}
        )
        return job

    def start_job(self, tenant_id: str, job_id: str) -> JobRecord:
        """Transitions a job to RUNNING."""
        return self._update_status(tenant_id, job_id, JobStatus.RUNNING)

    def update_progress(self, tenant_id: str, job_id: str, progress: float) -> JobRecord:
        """Updates progress fraction [0.0 - 1.0] of a running job."""
        with _jobs_lock:
            raw = self._store.get_job(tenant_id, job_id)
            if not raw:
                raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
            job = JobRecord(**raw)
            job.progress = max(0.0, min(1.0, float(progress)))
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._store.save_job(tenant_id, job_id, job.model_dump())
            return job

    def complete_job(self, tenant_id: str, job_id: str, result_meta: Optional[Dict[str, Any]] = None) -> JobRecord:
        """Marks a job as COMPLETED."""
        with _jobs_lock:
            raw = self._store.get_job(tenant_id, job_id)
            if not raw:
                raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
            job = JobRecord(**raw)
            job.status = JobStatus.COMPLETED
            job.progress = 1.0
            job.updated_at = datetime.now(timezone.utc).isoformat()
            job.completed_at = datetime.now(timezone.utc).isoformat()
            if result_meta:
                job.metadata.update(result_meta)
            self._store.save_job(tenant_id, job_id, job.model_dump())

            log_operations_audit(
                action="JOB_COMPLETED",
                status="SUCCESS",
                tenant_id=tenant_id,
                details={"job_id": job_id}
            )
            return job

    def fail_job(self, tenant_id: str, job_id: str, error_message: str) -> JobRecord:
        """Marks a job as FAILED."""
        with _jobs_lock:
            raw = self._store.get_job(tenant_id, job_id)
            if not raw:
                raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
            job = JobRecord(**raw)
            job.status = JobStatus.FAILED
            job.error = sanitize_secrets(error_message)
            job.updated_at = datetime.now(timezone.utc).isoformat()
            job.completed_at = datetime.now(timezone.utc).isoformat()
            self._store.save_job(tenant_id, job_id, job.model_dump())

            log_operations_audit(
                action="JOB_FAILED",
                status="FAILED",
                tenant_id=tenant_id,
                error_code=error_message[:48],
                details={"job_id": job_id}
            )
            return job

    def cancel_job(self, tenant_id: str, job_id: str) -> JobRecord:
        """Cooperatively cancels an active or queued job."""
        with _jobs_lock:
            raw = self._store.get_job(tenant_id, job_id)
            if not raw:
                raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
            job = JobRecord(**raw)
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                raise OperationsError(
                    JOB_ALREADY_COMPLETED,
                    f"Job '{job_id}' is already in terminal state '{job.status.value}'.",
                    status_code=400
                )
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.now(timezone.utc).isoformat()
            job.completed_at = datetime.now(timezone.utc).isoformat()
            self._store.save_job(tenant_id, job_id, job.model_dump())

            log_operations_audit(
                action="JOB_CANCELLED",
                status="CANCELLED",
                tenant_id=tenant_id,
                details={"job_id": job_id}
            )
            return job

    def _update_status(self, tenant_id: str, job_id: str, status: JobStatus) -> JobRecord:
        with _jobs_lock:
            raw = self._store.get_job(tenant_id, job_id)
            if not raw:
                raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
            job = JobRecord(**raw)
            job.status = status
            job.updated_at = datetime.now(timezone.utc).isoformat()
            self._store.save_job(tenant_id, job_id, job.model_dump())
            return job

    def get_job(self, tenant_id: str, job_id: str) -> JobRecord:
        """Retrieves a single job strictly scoped to the tenant."""
        raw = self._store.get_job(tenant_id, job_id)
        if not raw:
            raise OperationsError(JOB_NOT_FOUND, f"Job '{job_id}' not found.", status_code=404)
        return JobRecord(**raw)

    def list_jobs(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[JobRecord]:
        """Lists jobs with strict multi-tenant filtering."""
        raw_list = self._store.list_jobs(tenant_id=tenant_id, limit=limit)
        return [JobRecord(**j) for j in raw_list]
