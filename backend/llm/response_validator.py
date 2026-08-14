"""
Phase 2J — AI Response Validator
Validates and sanitizes raw model output, blocking forbidden tool execution or self-grant attempts.
"""
from typing import Optional, List, Dict, Any
import json

from llm.schemas import (
    LLMResponse,
    LLMToolIntent,
    LLMStatus,
    RiskLevel,
)
from llm.errors import (
    LLMError,
    MODEL_OUTPUT_BLOCKED,
    FORBIDDEN_PERMISSION_LEVEL,
)
from llm.sanitizer import redact_secrets, detect_prompt_injection

FORBIDDEN_TOOL_NAMES = {
    "EXECUTE_SHELL",
    "SHELL",
    "BASH",
    "SYSTEM",
    "RUN_COMMAND",
    "EXEC_PYTHON",
    "ARBITRARY_NETWORK",
    "INSTALL_PACKAGE",
    "SUDO",
    "ADMIN_OVERRIDE",
}

FORBIDDEN_PERMISSIONS = {"ADMIN", "EXECUTE", "NETWORK"}
MAX_RESPONSE_BYTES = 1024 * 1024  # 1MB


class ResponseValidator:
    """Validates and enforces security constraints on LLM completions."""

    @staticmethod
    def validate_response(response: LLMResponse) -> LLMResponse:
        # 1. Size constraint check
        if len(response.content.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise LLMError(
                MODEL_OUTPUT_BLOCKED,
                "Model response exceeded maximum allowed response size (1MB).",
            )

        # 2. Secret scrubbing in content
        clean_content, red_count = redact_secrets(response.content)
        response.content = clean_content
        if red_count > 0:
            response.safety.redacted_secrets_count += red_count
            response.safety.warnings.append(f"Sanitized {red_count} embedded secrets in model response.")

        # 3. Check for forbidden tool intents or self-authorization attempts
        validated_intents: List[LLMToolIntent] = []
        for intent in response.tool_intents:
            tool_name_upper = intent.tool_name.upper()

            # Forbidden execution tools
            if tool_name_upper in FORBIDDEN_TOOL_NAMES or "SHELL" in tool_name_upper:
                response.status = LLMStatus.BLOCKED
                raise LLMError(
                    MODEL_OUTPUT_BLOCKED,
                    f"Model attempted to invoke forbidden tool '{intent.tool_name}'.",
                )

            # Forbidden privilege escalation
            req_perm = (intent.requested_permission_level or "READ").upper()
            if req_perm in FORBIDDEN_PERMISSIONS:
                response.status = LLMStatus.BLOCKED
                raise LLMError(
                    FORBIDDEN_PERMISSION_LEVEL,
                    f"Model attempted forbidden permission escalation to '{req_perm}'.",
                )

            intent.is_authorized_intent = True
            validated_intents.append(intent)

        response.tool_intents = validated_intents

        # 4. If structured output is present, scrub secrets in keys/values
        if response.structured_output:
            try:
                dumped = json.dumps(response.structured_output)
                clean_dumped, _ = redact_secrets(dumped)
                response.structured_output = json.loads(clean_dumped)
            except Exception:
                pass

        return response
