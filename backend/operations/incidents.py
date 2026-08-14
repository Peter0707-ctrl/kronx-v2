"""
Phase 3.1 — Operational Incident Engine
Lightweight tracking of operational incidents and automated security violation triggers.
"""
import uuid
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from operations.schemas import IncidentRecord, IncidentStatus, Severity
from operations.errors import OperationsError, INCIDENT_NOT_FOUND
from operations.store import OperationsStore
from operations.audit import log_operations_audit
from llm.sanitizer import sanitize_secrets

_incidents_lock = threading.RLock()


class IncidentEngine:
    def __init__(self, store: Optional[OperationsStore] = None):
        self._store = store or OperationsStore()

    def create_incident(
        self,
        title: str,
        description: str,
        severity: Severity,
        source: str = "SYSTEM",
        tenant_id: Optional[str] = None,
    ) -> IncidentRecord:
        """Constructs and stores a new operational incident."""
        incident_id = f"inc_{uuid.uuid4().hex[:12]}"
        clean_title = sanitize_secrets(title[:120])
        clean_desc = sanitize_secrets(description[:500])

        inc = IncidentRecord(
            incident_id=incident_id,
            title=clean_title,
            description=clean_desc,
            severity=severity,
            status=IncidentStatus.OPEN,
            source=source,
            tenant_id=tenant_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with _incidents_lock:
            self._store.save_incident(incident_id, inc.model_dump())

        log_operations_audit(
            action="INCIDENT_CREATED",
            status=severity.value,
            tenant_id=tenant_id,
            details={"incident_id": incident_id, "title": clean_title, "severity": severity.value}
        )
        return inc

    def update_status(
        self,
        incident_id: str,
        status: IncidentStatus,
        notes: Optional[str] = None
    ) -> IncidentRecord:
        """Updates the status and notes of an existing incident."""
        with _incidents_lock:
            raw = self._store.get_incident(incident_id)
            if not raw:
                raise OperationsError(INCIDENT_NOT_FOUND, f"Incident '{incident_id}' not found.", status_code=404)
            inc = IncidentRecord(**raw)
            inc.status = status
            if notes:
                inc.resolution_notes = sanitize_secrets(notes[:500])
            if status in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                inc.resolved_at = datetime.now(timezone.utc).isoformat()

            self._store.save_incident(incident_id, inc.model_dump())

            log_operations_audit(
                action="INCIDENT_UPDATED",
                status=status.value,
                tenant_id=inc.tenant_id,
                details={"incident_id": incident_id, "new_status": status.value}
            )
            return inc

    def resolve_incident(self, incident_id: str, resolution_notes: str = "Resolved.") -> IncidentRecord:
        """Convenience method to resolve an incident."""
        return self.update_status(incident_id, IncidentStatus.RESOLVED, notes=resolution_notes)

    def get_incident(self, incident_id: str) -> IncidentRecord:
        """Retrieves a single incident record."""
        raw = self._store.get_incident(incident_id)
        if not raw:
            raise OperationsError(INCIDENT_NOT_FOUND, f"Incident '{incident_id}' not found.", status_code=404)
        return IncidentRecord(**raw)

    def list_incidents(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[IncidentRecord]:
        """Lists incidents with optional tenant filtering."""
        raw_list = self._store.list_incidents(tenant_id=tenant_id, limit=limit)
        return [IncidentRecord(**i) for i in raw_list]

    def check_security_trigger(self, event_type: str, details: Dict[str, Any], tenant_id: Optional[str] = None) -> Optional[IncidentRecord]:
        """Automatically generates an incident for high-risk security events."""
        if event_type in ["CROSS_TENANT_VIOLATION", "TENANT_MISMATCH"]:
            return self.create_incident(
                title="Cross-Tenant Access Attempt Detected",
                description=f"Blocked cross-tenant data access from tenant '{tenant_id}'.",
                severity=Severity.HIGH,
                source="SECURITY_GATEWAY",
                tenant_id=tenant_id,
            )
        if event_type in ["PATH_TRAVERSAL_ATTACK", "PATH_OUTSIDE_WORKSPACE"]:
            return self.create_incident(
                title="Workspace Path Traversal Attempt",
                description=f"Attempted directory traversal outside workspace boundary.",
                severity=Severity.HIGH,
                source="SANDBOX_VERIFIER",
                tenant_id=tenant_id,
            )
        if event_type in ["ROLE_ESCALATION_ATTEMPT", "UNAUTHORIZED_ADMIN_GRANT"]:
            return self.create_incident(
                title="Privilege Escalation Attempt Blocked",
                description="Model or client attempted unauthorized grant of elevated administrative roles.",
                severity=Severity.CRITICAL,
                source="AUTHORITY_ENGINE",
                tenant_id=tenant_id,
            )
        if event_type in ["STORE_CORRUPTED", "STORE_HASH_MISMATCH"]:
            return self.create_incident(
                title="Persistent Store Integrity Anomaly",
                description="Store corruption or hash mismatch detected during verification.",
                severity=Severity.HIGH,
                source="INTEGRITY_ENGINE",
                tenant_id=tenant_id,
            )
        return None
