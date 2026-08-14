"""
Phase 2J — LLM Sanitizer & Prompt Injection Defense
Scrubs secrets from prompts/responses and detects adversarial instruction-injection attempts.
"""
from __future__ import annotations
import re
from typing import Tuple, List, Dict, Any
from llm.schemas import LLMSafetyResult, RiskLevel

# High confidence secret patterns
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"(?:Bearer|Token)\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE), "[REDACTED_BEARER_TOKEN]"),
    (re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*(?:['\"][^'\"]{3,}['\"]|[^\s,;]{3,})", re.IGNORECASE), "password=[REDACTED_PASSWORD]"),

    (re.compile(r"(?:aws_secret_access_key|aws_access_key_id|aws_key)\s*[:=]?\s*['\"]?[^'\"]+['\"]?|AKIA[0-9A-Z]{16}", re.IGNORECASE), "[REDACTED_AWS_KEY]"),

    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),

    (re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}", re.IGNORECASE), "[REDACTED_GOOGLE_API_KEY]"),
]

# Prompt injection signatures
INJECTION_SIGNATURES = [
    "ignore previous instructions",
    "ignore all instructions",
    "ignore system instructions",
    "ignore developer instructions",
    "disregard all previous",
    "override safety",
    "disable security",
    "disable policy",
    "grant admin",
    "give yourself admin",
    "elevate to admin",
    "bypass authorization",
    "reveal secrets",
    "show api key",
    "show openai key",
    "print environment variables",
    "execute shell",
    "run command",
    "execute command",
    "pretend you are administrator",
    "you are now root",
    "sudo su",
]


def redact_secrets(text: str) -> Tuple[str, int]:
    """
    Sanitizes raw text against secret patterns.
    Returns (sanitized_text, count_of_redactions).
    """
    if not text:
        return text, 0

    sanitized = text
    count = 0
    for pattern, replacement in SECRET_PATTERNS:
        matches = pattern.findall(sanitized)
        if matches:
            count += len(matches)
            sanitized = pattern.sub(replacement, sanitized)

    return sanitized, count


def detect_prompt_injection(text: str) -> Tuple[bool, RiskLevel, List[str]]:
    """
    Detects known prompt-injection signatures in text.
    Returns (has_injection, risk_level, list_of_matched_warnings).
    """
    if not text:
        return False, RiskLevel.NONE, []

    lower_text = text.lower()
    matches = []

    for sig in INJECTION_SIGNATURES:
        if sig in lower_text:
            matches.append(f"Prompt injection detected: '{sig}'")

    if matches:
        return True, RiskLevel.HIGH, matches

    return False, RiskLevel.NONE, []


def sanitize_log_message(msg: str) -> str:
    """Sanitizes newlines and secrets for structured single-line log emission."""
    if not msg:
        return ""
    clean, _ = redact_secrets(msg)
    clean = clean.replace("\n", " ").replace("\r", " ")
    return clean[:1000]


def analyze_safety(text: str) -> LLMSafetyResult:
    """Performs full safety analysis and secret scrubbing on text."""
    clean_text, red_count = redact_secrets(text)
    has_inj, risk_lvl, warnings = detect_prompt_injection(text)

    violations = []
    if red_count > 0:
        warnings.append(f"Redacted {red_count} embedded credentials.")

    is_safe = True
    if has_inj:
        is_safe = False
        violations.extend(warnings)

    return LLMSafetyResult(
        is_safe=is_safe,
        risk_level=risk_lvl,
        violations=violations,
        warnings=warnings,
        redacted_secrets_count=red_count,
        prompt_injection_detected=has_inj,
    )


def sanitize_secrets(text: str) -> str:
    """Helper that returns sanitized text directly without the redaction count."""
    clean_text, _ = redact_secrets(text)
    return clean_text

