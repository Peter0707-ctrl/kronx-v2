"""
Phase 2J — LLM Orchestrator
Master coordinator for the LLM Gateway pipeline: auth, policy, routing, budgets, inference, validation, and audit.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, Optional, List, Iterator, Any

from llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMStatus,
    LLMInferenceRecord,
    LLMRouteDecision,
    LLMProvider,
    LLMCapability,
    RiskLevel,
)
from llm.errors import (
    LLMError,
    UNAUTHORIZED,
    FORBIDDEN,
    INFERENCE_CANCELLED,
    PROVIDER_UNAVAILABLE,
    MODEL_TIMEOUT,
)
from llm.policy import LLMPolicyEngine
from llm.budget import LLMBudgetManager
from llm.quota import LLMQuotaManager
from llm.router import ModelRouter
from llm.capabilities import ModelCapabilityRegistry
from llm.providers import ProviderRegistry, BaseLLMProvider
from llm.response_validator import ResponseValidator
from llm.sanitizer import analyze_safety, redact_secrets
from llm.streaming import SafeStreamManager
from llm.audit import log_llm_audit
from llm.store import LLMStore

_cancelled_requests = set()
_cancel_lock = threading.RLock()


class LLMOrchestrator:
    """End-to-end coordinator for secure AI model inference."""

    def __init__(
        self,
        store: Optional[LLMStore] = None,
        model_registry: Optional[ModelCapabilityRegistry] = None,
        provider_registry: Optional[ProviderRegistry] = None,
        budget_manager: Optional[LLMBudgetManager] = None,
        quota_manager: Optional[LLMQuotaManager] = None,
        policy_engine: Optional[LLMPolicyEngine] = None,
        router: Optional[ModelRouter] = None,
    ):
        self.store = store or LLMStore()
        self.model_registry = model_registry or ModelCapabilityRegistry()
        self.provider_registry = provider_registry or ProviderRegistry()
        self.budget_manager = budget_manager or LLMBudgetManager()
        self.quota_manager = quota_manager or LLMQuotaManager()
        self.policy_engine = policy_engine or LLMPolicyEngine()
        self.router = router or ModelRouter(self.model_registry)

    def cancel_request(self, request_id: str, tenant_id: str) -> bool:
        """Flags an active inference request as cancelled."""
        with _cancel_lock:
            _cancelled_requests.add(request_id)
        return True

    def _is_cancelled(self, request_id: str) -> bool:
        with _cancel_lock:
            return request_id in _cancelled_requests

    def execute(
        self,
        request: LLMRequest,
        is_authenticated: bool = True,
    ) -> LLMResponse:
        """Executes full inference lifecycle."""
        start_t = time.perf_counter()
        req_id = request.request_id
        t_id = request.tenant_id

        # 1. Server Policy & Identity Gate
        self.policy_engine.evaluate_request(request, is_authenticated=is_authenticated)

        # 2. Rate Quota Check
        self.quota_manager.check_and_increment(t_id)

        # 3. Budget Check (Estimate tokens based on character count)
        total_prompt_chars = sum(len(m.content) for m in request.messages)
        estimated_input_tokens = max(1, total_prompt_chars // 4)
        self.budget_manager.check_budget(t_id, estimated_input_tokens, request.max_tokens)

        # 4. Model Routing
        route_decision: LLMRouteDecision = self.router.route(request)
        provider_type = route_decision.provider
        model_id = route_decision.model
        request.model = model_id
        request.provider = provider_type

        # 5. Check Prompt Safety & Redact Secrets
        prompt_safety_warnings = []
        for msg in request.messages:
            safety_res = analyze_safety(msg.content)
            if not safety_res.is_safe:
                prompt_safety_warnings.extend(safety_res.warnings)
            clean_c, _ = redact_secrets(msg.content)
            msg.content = clean_c

        def _to_str(v: Any) -> str:
            return v.value if hasattr(v, "value") else str(v)

        # 6. Cancellation check before invocation
        if self._is_cancelled(req_id):
            dur = (time.perf_counter() - start_t) * 1000
            log_llm_audit(
                request_id=req_id,
                tenant_id=t_id,
                provider=_to_str(provider_type),
                model=model_id,
                capability="TEXT",
                status="CANCELLED",
                duration_ms=dur,
                reason_code=INFERENCE_CANCELLED,
            )
            raise LLMError(INFERENCE_CANCELLED, f"Inference request '{req_id}' was cancelled.")

        # 7. Provider Resolution & Execution with Retry
        # Ensure provider enum or string resolves
        prov_key = provider_type
        if isinstance(prov_key, str):
            try:
                prov_key = LLMProvider(prov_key)
            except Exception:
                pass
        provider: BaseLLMProvider = self.provider_registry.get_provider(prov_key)

        raw_response: Optional[LLMResponse] = None
        max_retries = 2
        last_err: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                raw_response = provider.generate(request)
                break
            except LLMError as e:
                # Do not retry non-transient security / capability errors
                if e.code in [UNAUTHORIZED, FORBIDDEN, INFERENCE_CANCELLED]:
                    raise
                last_err = e
                if attempt < max_retries:
                    time.sleep(0.05 * (2 ** attempt))
            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    time.sleep(0.05 * (2 ** attempt))

        if raw_response is None:
            dur = (time.perf_counter() - start_t) * 1000
            err_msg = str(last_err) if last_err else "Provider failed to generate response."
            log_llm_audit(
                request_id=req_id,
                tenant_id=t_id,
                provider=_to_str(provider_type),
                model=model_id,
                capability="TEXT",
                status="FAILED",
                duration_ms=dur,
                reason_code=PROVIDER_UNAVAILABLE,
            )
            raise LLMError(
                PROVIDER_UNAVAILABLE,
                f"Inference failed for model '{model_id}': {err_msg}",
            )

        # 8. AI Response Validation & Output Sandboxing
        validated_response = ResponseValidator.validate_response(raw_response)
        validated_response.safety.warnings.extend(prompt_safety_warnings)

        # 9. Record Actual Token Usage into Budget
        usage = self.budget_manager.record_usage(
            tenant_id=t_id,
            prompt_tokens=validated_response.usage.prompt_tokens,
            completion_tokens=validated_response.usage.completion_tokens,
        )
        validated_response.usage = usage

        dur_ms = (time.perf_counter() - start_t) * 1000
        validated_response.duration_ms = dur_ms

        # 10. Persist Record to Store
        record = LLMInferenceRecord(
            request_id=req_id,
            tenant_id=t_id,
            user_id=request.user_id,
            provider=provider_type,
            model=model_id,
            status=validated_response.status,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            risk_level=validated_response.safety.risk_level,
            duration_ms=dur_ms,
            error_code=None,
        )
        self.store.save_record(record)

        # 11. Structured Audit Log
        matched_cap_str = _to_str(route_decision.matched_capabilities[0]) if route_decision.matched_capabilities else "TEXT"
        log_llm_audit(
            request_id=req_id,
            tenant_id=t_id,
            provider=_to_str(provider_type),
            model=model_id,
            capability=matched_cap_str,
            status=_to_str(validated_response.status),
            duration_ms=dur_ms,
            input_token_count=usage.prompt_tokens,
            output_token_count=usage.completion_tokens,
            risk_level=_to_str(validated_response.safety.risk_level),
            reason_code="",
        )

        return validated_response


    def stream(
        self,
        request: LLMRequest,
        is_authenticated: bool = True,
    ) -> Iterator[str]:
        """Executes streaming inference wrapped with bounds and cancellation safety."""
        # Validate policy and routing
        self.policy_engine.evaluate_request(request, is_authenticated=is_authenticated)
        self.quota_manager.check_and_increment(request.tenant_id)
        route_decision = self.router.route(request)

        provider = self.provider_registry.get_provider(route_decision.provider)
        raw_stream = provider.stream(request)

        return SafeStreamManager.wrap_stream(
            raw_stream,
            request,
            is_cancelled_callback=lambda: self._is_cancelled(request.request_id),
        )
