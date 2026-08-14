"""
Phase 2I — Deterministic Decision Engine
Evaluates intent, context, risk, policy, and capability boundaries to produce structured decisions.
Fails closed on any security or authorization ambiguity.
"""
from __future__ import annotations
import uuid
from typing import List, Optional

from agent.schemas import (
    AgentIntent, AgentContext, AgentDecision, ReasoningMode,
    RiskLevel, IntentType
)
from agent.policy import AgentPolicyEngine


class DecisionEngine:
    """Evaluates contextual inputs to determine the next safe agent action."""

    @staticmethod
    def decide(
        request_id: str,
        intent: AgentIntent,
        context: AgentContext,
        is_workspace_authorized: bool,
        has_write_authorization: bool = False,
        selected_plan_id: Optional[str] = None,
    ) -> AgentDecision:
        decision_id = f"dec_{uuid.uuid4().hex[:10]}"

        # 1. Fail Closed on Unauthorized Workspace
        if not is_workspace_authorized:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.ANALYZE,
                requested_permissions=["READ"],
                allowed_actions=[],
                blocked_actions=intent.requested_capabilities,
                next_step="BLOCK",
                confidence=1.0,
                risk_level=RiskLevel.HIGH,
            )

        # 2. Ambiguous or Unknown Intent
        if intent.intent_type == IntentType.UNKNOWN or intent.confidence < 0.5:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.ANALYZE,
                requested_permissions=["READ"],
                allowed_actions=["READ_PROJECT"],
                blocked_actions=[],
                next_step="REQUIRE_CLARIFICATION",
                confidence=intent.confidence,
                risk_level=RiskLevel.LOW,
            )

        # 3. Policy Enforcement on Capabilities
        allowed_caps, blocked_caps, _ = AgentPolicyEngine.enforce_policy_on_capabilities(
            intent.requested_capabilities,
            has_write_authorization=has_write_authorization,
        )

        # 4. Modification Handling (Dry-Run First / Require Permission)
        if intent.intent_type in (IntentType.MODIFY, IntentType.REFACTOR):
            if not has_write_authorization:
                # Require explicit authorization before proceeding with write mutations
                next_step = "REQUIRE_PERMISSION" if not selected_plan_id else "PROPOSE_DRY_RUN"
            else:
                next_step = "MODIFY"

            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.MODIFY if has_write_authorization else ReasoningMode.DRY_RUN,
                selected_plan_id=selected_plan_id,
                requested_permissions=["WRITE" if has_write_authorization else "READ"],
                allowed_actions=allowed_caps,
                blocked_actions=blocked_caps,
                next_step=next_step,
                confidence=intent.confidence,
                risk_level=intent.risk_level,
            )

        # 5. Multimodal Capabilities Handling
        if intent.intent_type == IntentType.ANALYZE_IMAGE:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.ANALYZE,
                selected_plan_id=selected_plan_id,
                requested_permissions=["READ"],
                allowed_actions=allowed_caps,
                blocked_actions=blocked_caps,
                next_step="ANALYZE_IMAGE",
                confidence=intent.confidence,
                risk_level=intent.risk_level,
            )

        if intent.intent_type == IntentType.ANALYZE_DOCUMENT:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.ANALYZE,
                selected_plan_id=selected_plan_id,
                requested_permissions=["READ"],
                allowed_actions=allowed_caps,
                blocked_actions=blocked_caps,
                next_step="ANALYZE_DOCUMENT",
                confidence=intent.confidence,
                risk_level=intent.risk_level,
            )

        if intent.intent_type == IntentType.GENERATE_IMAGE:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.ANALYZE,
                selected_plan_id=selected_plan_id,
                requested_permissions=["READ"],
                allowed_actions=allowed_caps,
                blocked_actions=blocked_caps,
                next_step="GENERATE_IMAGE",
                confidence=intent.confidence,
                risk_level=intent.risk_level,
            )

        # 6. Verification Handling
        if intent.intent_type == IntentType.VERIFY:
            return AgentDecision(
                decision_id=decision_id,
                request_id=request_id,
                intent=intent,
                reasoning_mode=ReasoningMode.VERIFY,
                selected_plan_id=selected_plan_id,
                requested_permissions=["READ"],
                allowed_actions=allowed_caps,
                blocked_actions=blocked_caps,
                next_step="VERIFY",
                confidence=intent.confidence,
                risk_level=RiskLevel.LOW,
            )

        # 7. Read-Only Planning & Explanations
        return AgentDecision(
            decision_id=decision_id,
            request_id=request_id,
            intent=intent,
            reasoning_mode=ReasoningMode.ANALYZE,
            selected_plan_id=selected_plan_id,
            requested_permissions=["READ"],
            allowed_actions=allowed_caps,
            blocked_actions=blocked_caps,
            next_step="PLAN" if not selected_plan_id else "ANSWER",
            confidence=intent.confidence,
            risk_level=intent.risk_level,
        )

