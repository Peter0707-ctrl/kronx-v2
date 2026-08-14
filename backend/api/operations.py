"""
Phase 3.1 — Operations REST API Router
Exposes production observability, metrics, lifecycle, jobs, incidents, backups, recovery, diagnostics, and dashboard.
Strictly enforced by Phase 2G authentication, multi-tenant authorization, and role checks.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from auth.schemas import AuthenticationContext, UserRole
from api.auth import get_auth_context
from operations.orchestrator import OperationsOrchestrator
from operations.schemas import (
    LifecycleStatus,
    LifecycleState,
    HealthCheckResult,
    ReadinessEvaluation,
    OperationalEvent,
    DiagnosticReport,
    JobRecord,
    IncidentRecord,
    IncidentStatus,
    BackupRecord,
    RecoveryRequest,
    RecoveryResult,
    ConfigValidationResult,
    DashboardData,
)
from operations.errors import OperationsError, UNAUTHORIZED_OPERATION

operations_router = APIRouter(prefix="/api/operations", tags=["operations"])
_orchestrator = OperationsOrchestrator()


def _require_operator_role(context: AuthenticationContext) -> None:
    """Ensures caller has operational permissions (OPERATOR, ADMIN, or OWNER)."""
    allowed_roles = [UserRole.ADMIN, UserRole.OWNER, "OPERATOR", "ADMIN", "OWNER"]
    if context.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": UNAUTHORIZED_OPERATION, "message": "Operational privileges required for this action."}
        )


def _handle_operations_error(e: OperationsError) -> None:
    raise HTTPException(status_code=e.status_code, detail=e.to_dict())


# ------------------------------------------------------------------
# 1. Lifecycle Endpoints
# ------------------------------------------------------------------

@operations_router.get("/status", response_model=LifecycleStatus)
@operations_router.get("/lifecycle", response_model=LifecycleStatus)
@operations_router.get("/lifecycle/status", response_model=LifecycleStatus)
def get_lifecycle_status(context: AuthenticationContext = Depends(get_auth_context)):
    """Returns the current system lifecycle status."""
    return _orchestrator.lifecycle.get_status()


class DrainRequest(BaseModel):
    reason: Optional[str] = "Draining for operational maintenance."


@operations_router.post("/lifecycle/drain", response_model=LifecycleStatus)
def drain_system(
    body: DrainRequest,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Puts system into DRAINING state. Only operators allowed."""
    _require_operator_role(context)
    try:
        return _orchestrator.lifecycle.drain(reason=body.reason or "Draining invoked by operator.")
    except OperationsError as e:
        _handle_operations_error(e)


class RecoverRequest(BaseModel):
    reason: Optional[str] = "Operator recovery."


@operations_router.post("/lifecycle/recover", response_model=LifecycleStatus)
def recover_system(
    body: RecoverRequest,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Recovers system state back to READY. Only operators allowed."""
    _require_operator_role(context)
    try:
        return _orchestrator.lifecycle.recover(reason=body.reason or "Recovery invoked by operator.")
    except OperationsError as e:
        _handle_operations_error(e)


# ------------------------------------------------------------------
# 2. Metrics & Events Endpoints
# ------------------------------------------------------------------

@operations_router.get("/metrics", response_model=Dict[str, Any])
def get_metrics(context: AuthenticationContext = Depends(get_auth_context)):
    """Returns bounded operational metrics scoped to the caller."""
    return _orchestrator.metrics.get_summary(tenant_id=context.tenant_id)


@operations_router.get("/events", response_model=List[OperationalEvent])
def get_events(
    limit: int = Query(default=50, ge=1, le=100),
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Returns operational events for the caller's tenant."""
    is_operator = context.role in [UserRole.ADMIN, UserRole.OWNER, "OPERATOR", "ADMIN", "OWNER"]
    t_id = None if is_operator else context.tenant_id
    return _orchestrator.events.list_events(tenant_id=t_id, limit=limit)


# ------------------------------------------------------------------
# 3. Diagnostics Endpoints
# ------------------------------------------------------------------

@operations_router.post("/diagnostics/run", response_model=DiagnosticReport)
def run_diagnostics(context: AuthenticationContext = Depends(get_auth_context)):
    """Executes safe diagnostic checks. Only operators allowed."""
    _require_operator_role(context)
    return _orchestrator.diagnostics.run_diagnostics()


@operations_router.get("/diagnostics/{diagnostic_id}", response_model=DiagnosticReport)
def get_diagnostic_report(
    diagnostic_id: str,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Retrieves a diagnostic report by ID."""
    _require_operator_role(context)
    report = _orchestrator.diagnostics.get_diagnostic(diagnostic_id)
    if not report:
        raise HTTPException(status_code=404, detail={"code": "DIAGNOSTIC_NOT_FOUND", "message": "Report not found."})
    return report


# ------------------------------------------------------------------
# 4. Jobs Endpoints
# ------------------------------------------------------------------

@operations_router.get("/jobs", response_model=List[JobRecord])
def list_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Lists jobs strictly scoped to the tenant."""
    is_operator = context.role in [UserRole.ADMIN, UserRole.OWNER, "OPERATOR", "ADMIN", "OWNER"]
    t_id = None if is_operator else context.tenant_id
    return _orchestrator.jobs.list_jobs(tenant_id=t_id, limit=limit)


@operations_router.get("/jobs/{job_id}", response_model=JobRecord)
def get_job(
    job_id: str,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Retrieves a specific job for the tenant."""
    try:
        return _orchestrator.jobs.get_job(context.tenant_id, job_id)
    except OperationsError as e:
        _handle_operations_error(e)


@operations_router.post("/jobs/{job_id}/cancel", response_model=JobRecord)
def cancel_job(
    job_id: str,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Cooperatively cancels an ongoing job."""
    try:
        return _orchestrator.jobs.cancel_job(context.tenant_id, job_id)
    except OperationsError as e:
        _handle_operations_error(e)


# ------------------------------------------------------------------
# 5. Incidents Endpoints
# ------------------------------------------------------------------

@operations_router.get("/incidents", response_model=List[IncidentRecord])
def list_incidents(
    limit: int = Query(default=50, ge=1, le=100),
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Lists incidents filtered by tenant."""
    is_operator = context.role in [UserRole.ADMIN, UserRole.OWNER, "OPERATOR", "ADMIN", "OWNER"]
    t_id = None if is_operator else context.tenant_id
    return _orchestrator.incidents.list_incidents(tenant_id=t_id, limit=limit)


@operations_router.get("/incidents/{incident_id}", response_model=IncidentRecord)
def get_incident(
    incident_id: str,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Retrieves a specific incident."""
    try:
        inc = _orchestrator.incidents.get_incident(incident_id)
        if context.role not in [UserRole.ADMIN, UserRole.OWNER, "OPERATOR", "ADMIN", "OWNER"] and inc.tenant_id != context.tenant_id:
            raise HTTPException(status_code=404, detail={"code": "INCIDENT_NOT_FOUND", "message": "Incident not found."})
        return inc
    except OperationsError as e:
        _handle_operations_error(e)


class ResolveIncidentRequest(BaseModel):
    notes: Optional[str] = "Resolved."


@operations_router.post("/incidents/{incident_id}/resolve", response_model=IncidentRecord)
def resolve_incident(
    incident_id: str,
    body: ResolveIncidentRequest,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Resolves an operational incident. Only operators allowed."""
    _require_operator_role(context)
    try:
        return _orchestrator.incidents.resolve_incident(incident_id, resolution_notes=body.notes or "Resolved.")
    except OperationsError as e:
        _handle_operations_error(e)


# ------------------------------------------------------------------
# 6. Backups & Recovery Endpoints
# ------------------------------------------------------------------

@operations_router.get("/backups", response_model=List[BackupRecord])
def list_backups(
    store_name: Optional[str] = None,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Lists backup snapshots. Only operators allowed."""
    _require_operator_role(context)
    return _orchestrator.backup.list_backups(store_name=store_name)


class CreateBackupRequest(BaseModel):
    store_name: str


@operations_router.post("/backups/create", response_model=BackupRecord)
def create_backup(
    body: CreateBackupRequest,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Creates a verified atomic backup of a store. Only operators allowed."""
    _require_operator_role(context)
    try:
        return _orchestrator.backup.create_backup(body.store_name, tenant_scope=context.tenant_id)
    except OperationsError as e:
        _handle_operations_error(e)


@operations_router.post("/recovery/restore", response_model=RecoveryResult)
def restore_backup(
    body: RecoveryRequest,
    context: AuthenticationContext = Depends(get_auth_context)
):
    """Restores a store from verified backup. Only operators allowed."""
    _require_operator_role(context)
    try:
        role_str = context.role.value if hasattr(context.role, "value") else str(context.role)
        return _orchestrator.recovery.restore_backup(body, operator_role=role_str)
    except OperationsError as e:
        _handle_operations_error(e)


# ------------------------------------------------------------------
# 7. Configuration & Dashboard Endpoints
# ------------------------------------------------------------------

@operations_router.get("/configuration/status", response_model=ConfigValidationResult)
def get_configuration_status(context: AuthenticationContext = Depends(get_auth_context)):
    """Validates configuration without exposing secret values."""
    return _orchestrator.config.validate()


@operations_router.get("/dashboard", response_model=DashboardData)
def get_dashboard(context: AuthenticationContext = Depends(get_auth_context)):
    """Returns aggregated operational dashboard data."""
    return _orchestrator.get_dashboard(tenant_id=context.tenant_id)
