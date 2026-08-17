"""
Phase 2I.1 — Multimodal Sanitizer & Prompt Injection Neutralizer
Redacts secrets, neutralizes prompt injections into passive data, and sanitizes logs.
"""
import re
from typing import List, Tuple

# Secret patterns
SECRET_PATTERNS = [
    # Generic API keys / Tokens
    (re.compile(r'(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|client[_-]?secret)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]{12,})["\']?'), r'\1="[REDACTED_SECRET]"'),
    (re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s\n\r]{4,})["\']?'), r'\1="[REDACTED_PASSWORD]"'),
    # Specific Token Formats
    (re.compile(r'\b(sk-[a-zA-Z0-9]{20,})\b'), '[REDACTED_API_KEY]'),
    (re.compile(r'\b(kx-live-[a-zA-Z0-9]{8,})\b'), '[REDACTED_API_KEY]'),
    (re.compile(r'\b(ghp_[a-zA-Z0-9]{36})\b'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'\b(AKIA[0-9A-Z]{16})\b'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'\b(AIzaSy[a-zA-Z0-9_\-]{33})\b'), '[REDACTED_GOOGLE_KEY]'),
    # JWT Tokens
    (re.compile(r'\beyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b'), '[REDACTED_JWT]'),
    (re.compile(r'(?i)Bearer\s+([a-zA-Z0-9_\-\.]{20,})'), 'Bearer [REDACTED_TOKEN]'),
    # Private Key blocks
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), '[REDACTED_PRIVATE_KEY]'),
]

# Prompt injection signatures
PROMPT_INJECTION_PATTERNS = [
    (re.compile(r'(?i)ignore\s+(all\s+)?(previous|prior|system|safety|security)\s+(instructions|rules|policies|guidelines)'), "Instruction override pattern"),
    (re.compile(r'(?i)system\s+override\s*[:\-\.]'), "System override injection"),
    (re.compile(r'(?i)(grant|elevate|give\s+me|assign)\s+(admin|administrator|execute|network|write|root)'), "Privilege escalation attempt"),
    (re.compile(r'(?i)(disable|bypass|deactivate|override)\s+(security|policy|restrictions|safety|rules)'), "Security bypass attempt"),
    (re.compile(r'(?i)(read|print|dump|send|leak|exfiltrate|reveal)\s+(\.env|secrets|credentials|passwords|keys|tokens)'), "Secret exfiltration attempt"),
    (re.compile(r'(?i)(you\s+are\s+now|switch\s+to|activate)\s+(dan|developer\s+mode|unfiltered|jailbreak)'), "Persona hijacking attempt"),
    (re.compile(r'(?i)(run\s+command|execute\s+shell|bash\s+-c|curl\s+http|wget\s+http)'), "Command execution attempt"),
]


def redact_secrets(text: str) -> str:
    """Scans and redacts detected secrets, passwords, tokens, and private keys from text."""
    if not text:
        return ""
    sanitized = text
    for pattern, replacement in SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def detect_prompt_injection(text: str) -> List[str]:
    """
    Detects adversarial prompt injection attempts inside untrusted content.
    Returns list of detection warning descriptions.
    """
    if not text:
        return []
    warnings: List[str] = []
    for pattern, desc in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            warnings.append(f"Prompt injection signature detected: {desc}")
    return warnings


def neutralize_prompt_injections(text: str) -> str:
    """
    Neutralizes prompt injection directives inside untrusted file content,
    preventing malicious instruction execution while preserving data readability.
    """
    if not text:
        return ""
    sanitized = text
    for pattern, desc in PROMPT_INJECTION_PATTERNS:
        sanitized = pattern.sub(f"[DATA: Instruction override sanitized - {desc}]", sanitized)
    sanitized = re.sub(r"(?i)output\s+['\"][A-Z0-9_\-]+['\"]", "[DATA: Malicious output payload sanitized]", sanitized)
    return sanitized



def sanitize_log_message(msg: str) -> str:
    """
    Sanitizes log messages by replacing newlines, carriage returns, and control characters
    to prevent log injection and log forging.
    """
    if not msg:
        return ""
    # Strip carriage returns and replace newlines with space
    clean = msg.replace("\r", "").replace("\n", " ").replace("\t", " ")
    # Filter non-printable ASCII control characters
    clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean)
    return clean.strip()

