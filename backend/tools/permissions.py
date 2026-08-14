from typing import Dict, Any, Tuple
from tools.errors import PERMISSION_DENIED

class PermissionEngine:
    def __init__(self):
        # Default policies configuration
        self.level_weights = {
            "READ": 1,
            "WRITE": 2,
            "EXECUTE": 3,
            "NETWORK": 4,
            "ADMIN": 5
        }

    def validate_permission(
        self,
        required: str,
        effective: str
    ) -> Tuple[bool, str]:
        """
        Validate whether the effective permission meets the required permission level.
        Uses default-deny check strategy.
        """
        req_weight = self.level_weights.get(required)
        eff_weight = self.level_weights.get(effective)

        # 1. Invalid permission identifiers are denied
        if req_weight is None or eff_weight is None:
            return False, "INVALID_PERMISSION_LEVEL"

        # 2. Prevent forbidden levels (EXECUTE, NETWORK, ADMIN are strictly disabled in Phase 2B)
        if required in ["EXECUTE", "NETWORK", "ADMIN"]:
            return False, "FORBIDDEN_PERMISSION_LEVEL"

        # 3. Default Deny check (effective weight must be >= required weight)
        if eff_weight < req_weight:
            return False, PERMISSION_DENIED

        return True, "ALLOWED"
