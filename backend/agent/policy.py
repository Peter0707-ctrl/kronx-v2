"""
Phase 2I — Agent Policy Engine & Security Invariant Gate
Authoritative server-side policy evaluator for requested actions and permission boundaries.
The AI is NEVER allowed to self-grant permissions or elevate execution levels.
"""
from __future__ import annotations
from typing import Dict, List, Tuple
from agent.errors import (
    AgentError,
    FORBIDDEN_PERMISSION_LEVEL,
    PERMISSION_REQUIRED,
)
from agent.schemas import RiskLevel


class AgentPolicyEngine:
    """Evaluates requested capabilities and maps them to strict security constraints."""

    FORBIDDEN_PERMISSIONS = {"ADMIN", "EXECUTE", "NETWORK"}

    @staticmethod
    def evaluate_action_permission(requested_permission: str) -> Tuple[bool, str]:
        """
        Validates whether a permission level is allowed, requires permission, or is forbidden.
        Returns: (is_allowed, status_code)
        """
        perm = requested_permission.upper()
        if perm in AgentPolicyEngine.FORBIDDEN_PERMISSIONS:
            return False, FORBIDDEN_PERMISSION_LEVEL
        elif perm == "WRITE":
            return False, PERMISSION_REQUIRED
        elif perm == "READ":
            return True, "ALLOWED"
        return False, FORBIDDEN_PERMISSION_LEVEL

    @staticmethod
    def enforce_policy_on_capabilities(
        requested_capabilities: List[str],
        has_write_authorization: bool = False,
    ) -> Tuple[List[str], List[str], Dict[str, str]]:
        """
        Partitions requested capabilities into allowed and blocked lists based on server-side rules.
        Returns: (allowed_actions, blocked_actions, policy_map)
        """
        allowed: List[str] = []
        blocked: List[str] = []
        policy_map: Dict[str, str] = {}

        for cap in requested_capabilities:
            cap_u = cap.upper()
            if cap_u in ("EXECUTE_SHELL", "NETWORK_ACCESS", "ADMIN_GRANT"):
                blocked.append(cap)
                policy_map[cap] = FORBIDDEN_PERMISSION_LEVEL
            elif cap_u in ("APPLY_MODIFICATION", "WRITE_FILE"):
                if has_write_authorization:
                    allowed.append(cap)
                    policy_map[cap] = "ALLOWED_BY_AUTHORIZATION"
                else:
                    blocked.append(cap)
                    policy_map[cap] = PERMISSION_REQUIRED
            else:
                # Read-only or planning actions
                allowed.append(cap)
                policy_map[cap] = "ALLOWED"

        return allowed, blocked, policy_map
