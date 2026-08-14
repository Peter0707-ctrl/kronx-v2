"""
Phase 3.1 — Operational Event Engine
Emits and stores structured operational events with correlation IDs and strict multi-tenant scoping.
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from operations.schemas import OperationalEvent, EventType, Severity
from operations.store import OperationsStore
from operations.audit import log_operations_audit
from llm.sanitizer import sanitize_secrets


class OperationalEventManager:
    def __init__(self, store: Optional[OperationsStore] = None):
        self._store = store or OperationsStore()

    def emit_event(
        self,
        event_type: EventType,
        severity: Severity = Severity.LOW,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OperationalEvent:
        """Constructs, logs, and persists a structured operational event."""
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, str):
                    clean_meta[k] = sanitize_secrets(v)
                else:
                    clean_meta[k] = v

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        event = OperationalEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            severity=severity,
            request_id=request_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            metadata=clean_meta,
        )

        self._store.record_event(event.model_dump())

        log_operations_audit(
            action=event_type.value,
            status=severity.value,
            tenant_id=tenant_id,
            request_id=request_id,
            correlation_id=correlation_id,
            details={"event_id": event_id, **clean_meta},
        )
        return event

    def list_events(self, tenant_id: Optional[str] = None, limit: int = 50) -> List[OperationalEvent]:
        """Returns recent operational events, filtered by tenant if specified."""
        raw_events = self._store.get_events(tenant_id=tenant_id, limit=limit)
        return [OperationalEvent(**e) for e in raw_events]
