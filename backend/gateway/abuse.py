"""
Phase 2H — Abuse & Anomaly Detection Engine
Tracks repeated security violations and enforces temporary bounded cooldowns.
"""
from __future__ import annotations
import time
import threading
from typing import Dict
from gateway.errors import GatewayError, ABUSE_LIMIT_REACHED
from gateway.schemas import AbuseRecord

MAX_VIOLATIONS_BEFORE_COOLDOWN = 10
VIOLATION_WINDOW_SECONDS = 600  # 10 minutes
COOLDOWN_DURATION_SECONDS = 300  # 5 minutes
MAX_TRACKED_ABUSE_RECORDS = 2000

_abuse_lock = threading.RLock()


class AbuseDetector:
    """Detects repeated anomalous or hostile behaviors and enforces temporary cooldowns."""

    def __init__(self):
        self._records: Dict[str, AbuseRecord] = {}

    def check_abuse_status(self, identifier: str):
        """Checks whether an identifier is currently in a temporary cooldown."""
        now = time.time()
        with _abuse_lock:
            rec = self._records.get(identifier)
            if not rec:
                return

            if rec.blocked_until > now:
                remaining = int(rec.blocked_until - now)
                raise GatewayError(
                    code=ABUSE_LIMIT_REACHED,
                    detail=f"Security threshold reached. Temporary cooldown active for {remaining}s.",
                    status_code=429,
                )

    def record_violation(self, identifier: str, violation_type: str):
        """Records a security violation and activates cooldown if threshold exceeded."""
        now = time.time()
        with _abuse_lock:
            # Prune if too large
            if len(self._records) > MAX_TRACKED_ABUSE_RECORDS:
                expired = [k for k, r in self._records.items() if now - r.last_seen > VIOLATION_WINDOW_SECONDS * 2]
                for k in expired[:500]:
                    del self._records[k]

            rec = self._records.get(identifier)
            if not rec or (now - rec.last_seen > VIOLATION_WINDOW_SECONDS):
                self._records[identifier] = AbuseRecord(
                    identifier=identifier,
                    violation_count=1,
                    first_seen=now,
                    last_seen=now,
                )
            else:
                rec.violation_count += 1
                rec.last_seen = now
                if rec.violation_count >= MAX_VIOLATIONS_BEFORE_COOLDOWN:
                    rec.blocked_until = now + COOLDOWN_DURATION_SECONDS
                    self._records[identifier] = rec


abuse_detector = AbuseDetector()
