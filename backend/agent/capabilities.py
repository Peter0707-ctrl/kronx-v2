"""
Phase 2I — Agent Capability Registry
Maps high-level agent capabilities to underlying authorized phase engines.
No dynamic importing of arbitrary modules.
"""
from __future__ import annotations
from typing import Dict, Set
from agent.errors import AgentError, CAPABILITY_NOT_REGISTERED

REGISTERED_CAPABILITIES: Dict[str, str] = {
    "READ_PROJECT":          "workspace.store / tools.runtime",
    "SEARCH_CODE":           "tools.runtime",
    "ANALYZE_PROJECT":       "planner.planner",
    "CREATE_PLAN":           "planner.planner",
    "DRY_RUN":               "execution.orchestrator",
    "PROPOSE_MODIFICATION":  "modification.orchestrator",
    "APPLY_MODIFICATION":    "modification.orchestrator",
    "ROLLBACK_MODIFICATION": "modification.orchestrator",
    "VERIFY":                "verification.orchestrator",
    "ANALYZE_IMAGE":         "multimodal.image_analyzer",
    "ANALYZE_DOCUMENT":      "multimodal.document_analyzer",
    "ANALYZE_FILE":          "multimodal.file_analyzer",
    "OCR":                   "multimodal.ocr",
    "GENERATE_IMAGE":        "multimodal.generation",
    "DESIGN_GENERATION":     "multimodal.generation",
}



class CapabilityRegistry:
    """Registry and validator for safe underlying execution capabilities."""

    @staticmethod
    def validate_capability(capability_name: str) -> bool:
        return capability_name.upper() in REGISTERED_CAPABILITIES

    @staticmethod
    def get_registered_capabilities() -> Set[str]:
        return set(REGISTERED_CAPABILITIES.keys())

    @staticmethod
    def assert_capability_registered(capability_name: str):
        if not CapabilityRegistry.validate_capability(capability_name):
            raise AgentError(
                code=CAPABILITY_NOT_REGISTERED,
                detail=f"Capability '{capability_name}' is not a registered agent capability.",
                status_code=400,
            )
