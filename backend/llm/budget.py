"""
Phase 2J — LLM Budget & Token Accounting Engine
Enforces tenant and global token budgets and estimated cost bounds.
"""
import threading
from typing import Dict, Optional
from llm.schemas import LLMBudget, LLMUsage
from llm.errors import LLMError, BUDGET_EXCEEDED

_budget_lock = threading.RLock()

# Cost rates per 1k tokens (approximate reference rates)
PROMPT_COST_PER_1K = 0.0015
COMPLETION_COST_PER_1K = 0.0060

DEFAULT_MAX_INPUT = 1000000
DEFAULT_MAX_OUTPUT = 250000
DEFAULT_MAX_COST = 50.0


class LLMBudgetManager:
    """Manages token usage and monetary budget limits per tenant."""

    def __init__(self):
        self._budgets: Dict[str, LLMBudget] = {}

    def get_or_create_budget(self, tenant_id: str) -> LLMBudget:
        with _budget_lock:
            if tenant_id not in self._budgets:
                self._budgets[tenant_id] = LLMBudget(
                    tenant_id=tenant_id,
                    max_input_tokens=DEFAULT_MAX_INPUT,
                    max_output_tokens=DEFAULT_MAX_OUTPUT,
                    max_cost_usd=DEFAULT_MAX_COST,
                )
            return self._budgets[tenant_id]

    def set_budget_limits(
        self,
        tenant_id: str,
        max_input_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
    ):
        with _budget_lock:
            budget = self.get_or_create_budget(tenant_id)
            if max_input_tokens is not None:
                budget.max_input_tokens = max_input_tokens
            if max_output_tokens is not None:
                budget.max_output_tokens = max_output_tokens
            if max_cost_usd is not None:
                budget.max_cost_usd = max_cost_usd

    def check_budget(self, tenant_id: str, estimated_input_tokens: int, requested_max_output: int):
        """Verifies if the tenant has budget available before launching inference."""
        with _budget_lock:
            budget = self.get_or_create_budget(tenant_id)

            if budget.used_input_tokens + estimated_input_tokens > budget.max_input_tokens:
                raise LLMError(
                    BUDGET_EXCEEDED,
                    f"Tenant '{tenant_id}' exceeded input token budget limit.",
                    details={"used_input": budget.used_input_tokens, "limit": budget.max_input_tokens},
                )

            if budget.used_output_tokens + requested_max_output > budget.max_output_tokens:
                raise LLMError(
                    BUDGET_EXCEEDED,
                    f"Tenant '{tenant_id}' exceeded output token budget limit.",
                    details={"used_output": budget.used_output_tokens, "limit": budget.max_output_tokens},
                )

            if budget.used_cost_usd >= budget.max_cost_usd:
                raise LLMError(
                    BUDGET_EXCEEDED,
                    f"Tenant '{tenant_id}' exceeded monetary cost budget limit (${budget.max_cost_usd}).",
                    details={"used_cost": budget.used_cost_usd, "limit": budget.max_cost_usd},
                )

    def record_usage(
        self,
        tenant_id: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> LLMUsage:
        """Records actual token consumption and increments budget counters."""
        with _budget_lock:
            budget = self.get_or_create_budget(tenant_id)
            budget.used_input_tokens += prompt_tokens
            budget.used_output_tokens += completion_tokens

            cost = (prompt_tokens / 1000.0 * PROMPT_COST_PER_1K) + (
                completion_tokens / 1000.0 * COMPLETION_COST_PER_1K
            )
            budget.used_cost_usd += cost

            return LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                estimated_cost_usd=round(cost, 6),
            )
