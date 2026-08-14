"""
Phase 2I — Deterministic Intent Classification Engine
Classifies user requests into structured intents, confidence scores, capabilities, and risk levels.
Zero arbitrary code execution.
"""
from __future__ import annotations
import re
from typing import List, Tuple
from agent.schemas import IntentType, RiskLevel, AgentIntent

INTENT_KEYWORDS = {
    IntentType.GENERATE_IMAGE:   ["generate image", "create logo", "design mockup", "draw", "illustration", "generate visual", "poster", "create image", "generate diagram"],
    IntentType.ANALYZE_IMAGE:    ["screenshot", "diagram", "visual", "ui element", "look at this picture", "analyze picture", "analyze image", "inspect image", "read image", "ocr"],
    IntentType.ANALYZE_DOCUMENT: ["pdf", "document", "docx", "read doc", "analyze pdf", "read pdf", "extract sections", "read document"],

    IntentType.EXPLAIN:          ["explain", "how does", "what is", "walkthrough", "overview", "describe", "understand"],
    IntentType.DEBUG:            ["debug", "fix bug", "issue", "error", "failing", "exception", "traceback", "troubleshoot", "why is"],
    IntentType.REVIEW:           ["review", "audit", "inspect", "check code", "code quality", "security review", "lint"],
    IntentType.DESIGN:           ["design", "architecture", "blueprint", "model", "schema design", "plan feature"],
    IntentType.REFACTOR:         ["refactor", "clean up", "restructure", "simplify", "modularize", "extract method", "rename variable"],
    IntentType.DOCUMENT:         ["docstring", "readme", "comments", "generate docs", "api doc", "generate documentation"],
    IntentType.MODIFY:           ["modify", "change", "update", "patch", "edit file", "apply change", "write code", "fix"],
    IntentType.VERIFY:           ["verify", "validate", "production ready", "run checks", "readiness", "test health"],
    IntentType.ANALYZE:          ["analyze", "scan", "find", "search", "explore", "index", "list files", "dependencies"],
}



class IntentClassifier:
    """Classifies user prompts into deterministic structured intent representations."""

    @staticmethod
    def classify(objective: str) -> AgentIntent:
        if not objective or not objective.strip():
            return AgentIntent(
                intent_type=IntentType.UNKNOWN,
                confidence=0.0,
                normalized_objective="",
                requested_capabilities=[],
                risk_level=RiskLevel.LOW,
            )

        norm_obj = objective.strip().lower()
        matched_scores: List[Tuple[IntentType, float]] = []

        for itype, keywords in INTENT_KEYWORDS.items():
            matches = 0
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", norm_obj):
                    matches += 1
            if matches > 0:
                conf = min(0.5 + (matches * 0.25), 0.98)
                matched_scores.append((itype, conf))

        if not matched_scores:
            # Fallback to general ANALYZE if words present, else UNKNOWN
            if len(norm_obj.split()) >= 2:
                intent_type = IntentType.ANALYZE
                confidence = 0.65
            else:
                intent_type = IntentType.UNKNOWN
                confidence = 0.3
        else:
            # Sort by highest confidence
            matched_scores.sort(key=lambda x: x[1], reverse=True)
            intent_type, confidence = matched_scores[0]

        # Determine capabilities and risk
        caps, risk = IntentClassifier._resolve_capabilities_and_risk(intent_type, norm_obj)

        return AgentIntent(
            intent_type=intent_type,
            confidence=round(confidence, 2),
            normalized_objective=norm_obj[:500],
            requested_capabilities=caps,
            risk_level=risk,
        )

    @staticmethod
    def _resolve_capabilities_and_risk(itype: IntentType, norm_obj: str) -> Tuple[List[str], RiskLevel]:
        if itype == IntentType.ANALYZE_IMAGE:
            return ["READ_PROJECT", "ANALYZE_IMAGE", "OCR"], RiskLevel.LOW
        elif itype == IntentType.ANALYZE_DOCUMENT:
            return ["READ_PROJECT", "ANALYZE_DOCUMENT"], RiskLevel.LOW
        elif itype == IntentType.GENERATE_IMAGE:
            return ["READ_PROJECT", "GENERATE_IMAGE", "DESIGN_GENERATION"], RiskLevel.LOW
        elif itype in (IntentType.MODIFY, IntentType.REFACTOR):
            return ["READ_PROJECT", "ANALYZE_PROJECT", "CREATE_PLAN", "PROPOSE_MODIFICATION", "DRY_RUN", "VERIFY"], RiskLevel.HIGH
        elif itype == IntentType.VERIFY:
            return ["READ_PROJECT", "VERIFY"], RiskLevel.LOW
        elif itype == IntentType.DEBUG:
            return ["READ_PROJECT", "SEARCH_CODE", "ANALYZE_PROJECT"], RiskLevel.MEDIUM
        elif itype == IntentType.REVIEW:
            return ["READ_PROJECT", "ANALYZE_PROJECT"], RiskLevel.LOW
        elif itype in (IntentType.EXPLAIN, IntentType.DOCUMENT, IntentType.DESIGN):
            return ["READ_PROJECT", "ANALYZE_PROJECT"], RiskLevel.LOW
        elif itype == IntentType.ANALYZE:
            return ["READ_PROJECT", "SEARCH_CODE", "ANALYZE_PROJECT"], RiskLevel.LOW
        return ["READ_PROJECT"], RiskLevel.LOW

