"""
Phase 2C — Risk Engine
Deterministic risk classification for planning objectives and task sets.
Flags any action requiring WRITE/EXECUTE/NETWORK/ADMIN as BLOCKED_REQUIRES_PERMISSION.
"""
from __future__ import annotations
import uuid
from typing import List, Tuple

from planner.schemas import (
    RiskRecord, RiskLevel, PlanningTask, TaskType,
    MAX_RISKS
)

# Keywords that indicate elevated risk in the objective text
_CRITICAL_KEYWORDS = [
    "delete", "drop database", "drop table", "truncate", "wipe",
    "payment", "auth", "authentication", "credential", "password",
    "private key", "secret", "encryption", "deploy", "production",
    "rollback", "migration", "shell", "exec", "subprocess",
]
_HIGH_KEYWORDS = [
    "modify", "edit", "write", "update", "change", "refactor",
    "install", "upgrade", "dependency", "package",
    "api contract", "breaking change", "external api", "webhook",
    "database", "migration", "schema",
]
_MEDIUM_KEYWORDS = [
    "add", "create", "remove", "rename", "move",
    "configuration", "config", "environment", "route",
    "test", "lint", "format",
]

# Permission requirements
_BLOCKED_PERMISSIONS = {"WRITE", "EXECUTE", "NETWORK", "ADMIN"}


class RiskEngine:

    def evaluate(
        self,
        objective: str,
        tasks: List[PlanningTask],
    ) -> Tuple[List[RiskRecord], List[str]]:
        """
        Returns (risk_records, blocked_actions).
        blocked_actions lists human-readable descriptions of actions that
        cannot proceed without explicit permission grants.
        """
        risks: List[RiskRecord] = []
        blocked: List[str] = []

        obj_lower = objective.lower()

        # 1. Objective-level keyword risk scan
        for kw in _CRITICAL_KEYWORDS:
            if kw in obj_lower:
                risks.append(RiskRecord(
                    risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                    level=RiskLevel.CRITICAL,
                    description=f"Objective contains high-risk keyword '{kw}'.",
                    category="objective_content",
                    impact="May require irreversible or security-sensitive operations.",
                    blocked=True,
                ))
                blocked.append(f"Operation touching '{kw}' requires explicit permission.")
                break  # one critical is enough to flag at task scan level

        if not any(r.level == RiskLevel.CRITICAL for r in risks):
            for kw in _HIGH_KEYWORDS:
                if kw in obj_lower:
                    risks.append(RiskRecord(
                        risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                        level=RiskLevel.HIGH,
                        description=f"Objective involves a potentially impactful operation: '{kw}'.",
                        category="objective_content",
                        impact="May alter system behaviour or data.",
                        blocked=False,
                    ))
                    break

        if not any(r.level in (RiskLevel.CRITICAL, RiskLevel.HIGH) for r in risks):
            for kw in _MEDIUM_KEYWORDS:
                if kw in obj_lower:
                    risks.append(RiskRecord(
                        risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                        level=RiskLevel.MEDIUM,
                        description=f"Objective involves a moderate-impact change: '{kw}'.",
                        category="objective_content",
                        impact="Localised change; verify tests after applying.",
                        blocked=False,
                    ))
                    break

        # 2. Task-level permission analysis
        for task in tasks:
            for tool in task.required_tools:
                if tool.upper() in _BLOCKED_PERMISSIONS or tool in (
                    "create_file", "edit_file", "write_file",
                    "execute_command", "network_request",
                ):
                    blocked_msg = (
                        f"Task '{task.task_id}' requires blocked capability: '{tool}'."
                    )
                    blocked.append(blocked_msg)
                    risks.append(RiskRecord(
                        risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                        level=RiskLevel.CRITICAL,
                        description=blocked_msg,
                        category="permission_escalation",
                        impact="BLOCKED — would violate Phase 2B default-deny policy.",
                        blocked=True,
                    ))

        # 3. WAIT_FOR_PERMISSION tasks always carry a MEDIUM risk annotation
        for task in tasks:
            if task.task_type == TaskType.WAIT_FOR_PERMISSION:
                risks.append(RiskRecord(
                    risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                    level=RiskLevel.MEDIUM,
                    description=f"Task '{task.task_id}' explicitly requires human permission before proceeding.",
                    category="approval_gate",
                    impact="Plan cannot auto-proceed past this task.",
                    blocked=False,
                ))

        # 4. Default LOW risk if nothing else flagged
        if not risks:
            risks.append(RiskRecord(
                risk_id=f"risk_{uuid.uuid4().hex[:6]}",
                level=RiskLevel.LOW,
                description="No elevated risks identified for this planning objective.",
                category="general",
                impact="Minimal expected impact.",
                blocked=False,
            ))

        return risks[:MAX_RISKS], blocked
