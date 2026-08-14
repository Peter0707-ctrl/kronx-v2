from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from workspace.manager import WorkspaceManager
from workspace.schema import Workspace, ScanJob, ProjectProfile
from utils.logger import logger

router = APIRouter()
manager = WorkspaceManager()

class WorkspaceRegisterRequest(BaseModel):
    root_path: str

class ScanTriggerRequest(BaseModel):
    workspace_id: str

@router.post("/workspace", response_model=Workspace)
async def register_workspace(payload: WorkspaceRegisterRequest):
    """Register and authorize a directory path as a safe workspace."""
    try:
        ws = manager.register_workspace(payload.root_path)
        return ws
    except ValueError as ve:
        if str(ve) == "PATH_OUTSIDE_WORKSPACE":
            raise HTTPException(status_code=403, detail="PATH_OUTSIDE_WORKSPACE")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to register workspace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error registering workspace.")

@router.post("/workspace/scan", response_model=ScanJob)
async def trigger_scan(payload: ScanTriggerRequest):
    """Trigger a non-blocking background workspace scan job."""
    try:
        job = manager.queue_scan(payload.workspace_id)
        return job
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to queue workspace scan: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error queuing scan.")

@router.get("/workspace/scan/{scan_id}", response_model=ScanJob)
async def get_scan_status(scan_id: str):
    """Retrieve workspace scan job status and progress."""
    job = manager.get_job(scan_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found.")
    return job

@router.post("/workspace/scan/{scan_id}/cancel", response_model=ScanJob)
async def cancel_scan(scan_id: str):
    """Request cooperative cancellation of a running scan job."""
    try:
        job = manager.cancel_job(scan_id)
        return job
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to cancel scan job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error cancelling scan.")

@router.get("/workspace/{workspace_id}/profile", response_model=ProjectProfile)
async def get_project_profile(workspace_id: str):
    """Retrieve the generated ProjectProfile result for an authorized workspace."""
    # Retrieve the last successful completed scan job for this workspace
    # Since jobs are stored in store, we scan all jobs
    all_jobs_dict = manager.store._load().get("jobs", {})
    last_completed_job = None
    
    for job_id, job in all_jobs_dict.items():
        if job.get("workspace_id") == workspace_id and job.get("status") == "COMPLETED":
            # Compare completed_at times
            if not last_completed_job or job.get("completed_at", "") > last_completed_job.get("completed_at", ""):
                last_completed_job = job
                
    if not last_completed_job or not last_completed_job.get("result"):
        raise HTTPException(status_code=404, detail="Project profile not found. Please run a successful scan first.")
        
    return ProjectProfile(**last_completed_job["result"])
