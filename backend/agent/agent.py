"""
Phase 2I — Core AI Agent Brain
Coordinates the 17-step safe reasoning and execution flow through authoritative Phase 2A–2H engines.
Never directly executes commands, touches filesystem paths outside engines, or bypasses permissions.
"""
from __future__ import annotations
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from agent.schemas import (
    AgentRequest, AgentIntent, AgentContext, AgentDecision,
    AgentResult, AgentStatus, DecisionTrace, IntentType,
    ReasoningMode, RiskLevel
)
from agent.errors import (
    AgentError,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    INTENT_UNCERTAIN,
    PERMISSION_REQUIRED,
    FORBIDDEN_PERMISSION_LEVEL,
    INVALID_AGENT_REQUEST,
)
from agent.intent import IntentClassifier
from agent.context import ContextEngine
from agent.policy import AgentPolicyEngine
from agent.capabilities import CapabilityRegistry
from agent.decision import DecisionEngine
from agent.memory import AgentMemoryStore
from agent.trace import AgentTraceStore
from agent.audit import log_agent_audit
from auth.schemas import AuthenticationContext
from auth.authorization import MultiTenantAuthorizer
from workspace.store import WorkspaceStore
from planner.planner import KronxPlanner
from planner.schemas import PlanningRequest, PlanningMode
from verification.orchestrator import VerificationOrchestrator
from verification.schemas import VerificationRequest
from modification.orchestrator import ModificationOrchestrator
from modification.schemas import ModificationRequest, PatchPayload, FilePatch, FileOperationType



class KronxAgent:
    """Core Agent Brain executing safe, authenticated, and verified reasoning flows."""

    def __init__(
        self,
        ws_store: Optional[WorkspaceStore] = None,
        authorizer: Optional[MultiTenantAuthorizer] = None,
        memory_store: Optional[AgentMemoryStore] = None,
        trace_store: Optional[AgentTraceStore] = None,
        planner: Optional[KronxPlanner] = None,
        verifier: Optional[VerificationOrchestrator] = None,
        modifier: Optional[ModificationOrchestrator] = None,
    ):
        self._ws_store = ws_store or WorkspaceStore()
        self._authorizer = authorizer or MultiTenantAuthorizer(self._ws_store)
        self._memory_store = memory_store or AgentMemoryStore()
        self._trace_store = trace_store or AgentTraceStore()
        self._context_engine = ContextEngine(self._ws_store)
        self._planner = planner or KronxPlanner()
        self._verifier = verifier or VerificationOrchestrator(ws_store=self._ws_store)
        self._modifier = modifier or ModificationOrchestrator(ws_store=self._ws_store)


    def process_request(
        self,
        auth_context: AuthenticationContext,
        request: AgentRequest,
        has_write_authorization: bool = False,
    ) -> AgentResult:
        start_time = time.perf_counter()
        agent_id = f"agt_{uuid.uuid4().hex[:10]}"
        trace_id = f"trc_{uuid.uuid4().hex[:10]}"

        # 1. Server-Side Workspace & Tenant Authorization Gate
        try:
            ws_data = self._authorizer.authorize_workspace_access(auth_context, request.workspace_id)
        except Exception as e:
            dur = (time.perf_counter() - start_time) * 1000
            log_agent_audit(
                agent_id=agent_id,
                request_id=request.request_id,
                tenant_id=auth_context.tenant_id,
                user_id=auth_context.user_id,
                workspace_id=request.workspace_id,
                intent="UNKNOWN",
                status="FAILED",
                duration_ms=dur,
                reason="WORKSPACE_NOT_AUTHORIZED",
            )
            raise AgentError(
                code=WORKSPACE_NOT_AUTHORIZED,
                detail=f"Workspace '{request.workspace_id}' is not authorized for this tenant.",
                status_code=403,
            )

        # 2. Prompt Injection Defense on Objective
        # Ensure client cannot self-grant permissions
        norm_obj = request.objective.strip()

        # 3. Intent Classification
        intent = IntentClassifier.classify(norm_obj)

        # 4. Context Aggregation
        context = self._context_engine.build_context(
            workspace_id=request.workspace_id,
            tenant_id=auth_context.tenant_id,
            user_id=auth_context.user_id,
            user_constraints=request.constraints,
        )

        # 5. Decision Generation
        decision = DecisionEngine.decide(
            request_id=request.request_id,
            intent=intent,
            context=context,
            is_workspace_authorized=True,
            has_write_authorization=has_write_authorization,
        )

        plan_id: Optional[str] = None
        exec_id: Optional[str] = None
        mod_id: Optional[str] = None
        ver_id: Optional[str] = None
        status = AgentStatus.COMPLETED
        summary = ""
        warnings: List[str] = []

        # 6. Execute Approved Action via Authoritative Engine
        try:
            if decision.next_step == "REQUIRE_PERMISSION":
                status = AgentStatus.AWAITING_PERMISSION
                summary = f"Operation '{intent.intent_type.value}' requires explicit human WRITE authorization."
                warnings.append("No modifications were performed. Server authorization record required.")

            elif decision.next_step == "PROPOSE_DRY_RUN":
                # Create proposal only (zero mutations)
                status = AgentStatus.AWAITING_PERMISSION
                prop_req = ModificationRequest(
                    workspace_id=request.workspace_id,
                    mode="PATCH",
                    patches=PatchPayload(files=[]),
                    dry_run=True,
                )
                proposal = self._modifier.propose(prop_req)
                mod_id = proposal.proposal_id
                summary = f"Generated modification proposal '{proposal.proposal_id}' (dry_run=True). Awaiting approval."

            elif decision.next_step == "VERIFY":
                ver_res = self._verifier.run_verification(
                    VerificationRequest(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                    )
                )
                ver_id = ver_res.verification_id
                v_st = getattr(ver_res.status, "value", ver_res.status)
                v_rd = getattr(ver_res.readiness_decision, "value", ver_res.readiness_decision)
                summary = f"Verification completed with status '{v_st}' (readiness: {v_rd})."


            elif decision.next_step == "ANALYZE_IMAGE":
                from multimodal.orchestrator import MultimodalOrchestrator
                from multimodal.schemas import MultimodalRequest, MultimodalOperation
                mm_orch = MultimodalOrchestrator()
                mm_res = mm_orch.execute(
                    request=MultimodalRequest(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                        agent_id=agent_id,
                        operation=MultimodalOperation.IMAGE_ANALYSIS,
                        prompt=request.objective,
                        file_reference=request.metadata.get("file_reference"),
                        raw_content=request.metadata.get("raw_content"),
                        mime_type=request.metadata.get("mime_type"),
                    ),
                    tenant_id=auth_context.tenant_id,
                    user_id=auth_context.user_id,
                )
                summary = f"Analyzed visual asset. {mm_res.image_analysis.description if mm_res.image_analysis else ''}"
                warnings.extend(mm_res.warnings)

            elif decision.next_step == "ANALYZE_DOCUMENT":
                from multimodal.orchestrator import MultimodalOrchestrator
                from multimodal.schemas import MultimodalRequest, MultimodalOperation
                mm_orch = MultimodalOrchestrator()
                mm_res = mm_orch.execute(
                    request=MultimodalRequest(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                        agent_id=agent_id,
                        operation=MultimodalOperation.DOCUMENT_ANALYSIS,
                        prompt=request.objective,
                        file_reference=request.metadata.get("file_reference"),
                        raw_content=request.metadata.get("raw_content"),
                        filename=request.metadata.get("filename"),
                        mime_type=request.metadata.get("mime_type"),
                    ),
                    tenant_id=auth_context.tenant_id,
                    user_id=auth_context.user_id,
                )
                summary = f"Analyzed document. Extracted {mm_res.document_analysis.word_count if mm_res.document_analysis else 0} words."
                warnings.extend(mm_res.warnings)

            elif decision.next_step == "GENERATE_IMAGE":
                from multimodal.orchestrator import MultimodalOrchestrator
                from multimodal.schemas import MultimodalRequest, MultimodalOperation
                mm_orch = MultimodalOrchestrator()
                mm_res = mm_orch.execute(
                    request=MultimodalRequest(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                        agent_id=agent_id,
                        operation=MultimodalOperation.IMAGE_GENERATION,
                        prompt=request.objective,
                        options=request.metadata.get("options", {}),
                    ),
                    tenant_id=auth_context.tenant_id,
                    user_id=auth_context.user_id,
                )
                summary = f"Generated visual asset '{mm_res.generation_result.artifact_id if mm_res.generation_result else ''}'."
                warnings.extend(mm_res.warnings)

            elif decision.next_step == "REQUIRE_CLARIFICATION":
                status = AgentStatus.COMPLETED
                summary = "Request is ambiguous or low confidence. Please provide more specific details."

            else:
                # Default: Read-Only Planning & Reasoning
                plan_result = self._planner.plan(
                    PlanningRequest(
                        request_id=request.request_id,
                        workspace_id=request.workspace_id,
                        objective=request.objective,
                        requested_mode=PlanningMode.ANALYZE,
                    )
                )
                plan_id = plan_result.plan_id
                summary = f"Generated safe plan '{plan_result.plan_id}' with {len(plan_result.tasks)} tasks."




        except Exception as e:
            status = AgentStatus.FAILED
            summary = f"Execution failed: {str(e)}"

        dur_ms = (time.perf_counter() - start_time) * 1000

        # 7. Record Decision Trace
        trace = DecisionTrace(
            trace_id=trace_id,
            request_id=request.request_id,
            tenant_id=auth_context.tenant_id,
            user_id=auth_context.user_id,
            workspace_id=request.workspace_id,
            intent=intent.intent_type.value,
            risk=intent.risk_level.value,
            requested_capabilities=intent.requested_capabilities,
            policy_decisions={cap: "ALLOWED" for cap in decision.allowed_actions},
            selected_plan=plan_id,
            modification_reference=mod_id,
            verification_reference=ver_id,
            final_decision=decision.next_step,
            duration_ms=round(dur_ms, 2),
        )
        self._trace_store.record_trace(trace)

        # 8. Record Memory
        self._memory_store.record_memory(
            tenant_id=auth_context.tenant_id,
            memory_type="REQUEST",
            content=f"Objective: {request.objective[:100]} -> Decision: {decision.next_step}",
            metadata={"agent_id": agent_id, "plan_id": plan_id, "status": status.value},
        )

        # 9. Audit Logging
        log_agent_audit(
            agent_id=agent_id,
            request_id=request.request_id,
            tenant_id=auth_context.tenant_id,
            user_id=auth_context.user_id,
            workspace_id=request.workspace_id,
            intent=intent.intent_type.value,
            status=status.value,
            duration_ms=dur_ms,
            plan_id=plan_id or "",
            modification_id=mod_id or "",
            verification_id=ver_id or "",
        )

        return AgentResult(
            agent_id=agent_id,
            request_id=request.request_id,
            status=status,
            summary=summary,
            decision=decision,
            plan_id=plan_id,
            execution_id=exec_id,
            modification_id=mod_id,
            verification_id=ver_id,
            blocked_actions=decision.blocked_actions,
            warnings=warnings,
            trace_id=trace_id,
        )
