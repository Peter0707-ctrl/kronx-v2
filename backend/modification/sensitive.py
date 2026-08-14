"""
Phase 2E — Sensitive File & Defensive Secret Detection
Enforces strict restrictions against writing to sensitive, binary, generated, and security-critical files.
Performs defensive secret scanning on patch content.
"""
from __future__ import annotations
import os
import re
from typing import List, Tuple, Optional

# ------------------------------------------------------------------
# Sensitive Filename Patterns
# ------------------------------------------------------------------
SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r'^\.env(?:\..*)?$', re.IGNORECASE),
    re.compile(r'^credentials(?:\..*)?$', re.IGNORECASE),
    re.compile(r'^secrets(?:\..*)?$', re.IGNORECASE),
    re.compile(r'^id_(?:rsa|dsa|ecdsa|ed25519)$', re.IGNORECASE),
    re.compile(r'^.*\.pem$', re.IGNORECASE),
    re.compile(r'^.*\.key$', re.IGNORECASE),
    re.compile(r'^.*\.p12$', re.IGNORECASE),
    re.compile(r'^.*\.pfx$', re.IGNORECASE),
    re.compile(r'^.*\.kdbx$', re.IGNORECASE),
    re.compile(r'^private_key(?:\..*)?$', re.IGNORECASE),
    re.compile(r'^db_password$', re.IGNORECASE),
]

# ------------------------------------------------------------------
# Protected Infrastructure / Store Files
# ------------------------------------------------------------------
PROTECTED_SERVER_FILES = frozenset([
    "workspace_store.json",
    "planner_store.json",
    "execution_store.json",
    "modification_store.json",
    "authorization_store.json",
    "rollback_store.json",
    "memory_store.json",
    "kronx_app.log",
    "tools_audit.log",
    "requirements.txt",
    "Procfile",
    "railway.toml",
])

# ------------------------------------------------------------------
# Generated / Ignored Directories
# ------------------------------------------------------------------
GENERATED_DIRS = frozenset([
    ".git", "node_modules", "vendor", "__pycache__", "dist", "build",
    "coverage", ".next", "target", "venv", ".venv", "env", "bin", "obj",
    ".pytest_cache", ".mypy_cache"
])

# ------------------------------------------------------------------
# Binary File Extensions
# ------------------------------------------------------------------
BINARY_EXTENSIONS = frozenset([
    ".exe", ".dll", ".sys", ".so", ".dylib", ".bin", ".pyc", ".pyo", ".pyd",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
    ".iso", ".dmg", ".wasm", ".class", ".jar", ".lib", ".o", ".a"
])

# ------------------------------------------------------------------
# Defensive Secret Patterns in Patch Content
# ------------------------------------------------------------------
SECRET_CONTENT_PATTERNS = [
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----', re.IGNORECASE),
    re.compile(r'AKIA[0-9A-Z]{16}'),                          # AWS Access Key ID
    re.compile(r'ghp_[A-Za-z0-9]{36}'),                       # GitHub Personal Access Token
    re.compile(r'github_pat_[A-Za-z0-9_]{40,}'),              # GitHub Fine-grained PAT
    re.compile(r'sk-[a-zA-Z0-9]{32,}'),                       # OpenAI API Key
    re.compile(r'gsk_[a-zA-Z0-9]{40,}'),                      # Groq API Key
    re.compile(r'(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']', re.IGNORECASE),
    re.compile(r'postgres(?:ql)?:\/\/[^:]+:[^@]+@[^\/]+\/', re.IGNORECASE),  # DB URL with embedded password
    re.compile(r'mysql:\/\/[^:]+:[^@]+@[^\/]+\/', re.IGNORECASE),
]


class SensitiveFileDetector:
    """Security classifier for sensitive, generated, binary, and secret content."""

    @staticmethod
    def is_sensitive_path(relative_path: str) -> Tuple[bool, str]:
        """Check if relative path matches any sensitive file patterns."""
        normalized = relative_path.replace("\\", "/").strip("/")
        basename = os.path.basename(normalized)
        
        # 1. Match basename against regex patterns
        for pattern in SENSITIVE_FILENAME_PATTERNS:
            if pattern.match(basename):
                return True, f"Sensitive filename pattern matched: '{basename}'"

        # 2. Check if it targets protected server stores
        if basename in PROTECTED_SERVER_FILES:
            return True, f"Target is a protected server storage/configuration file: '{basename}'"

        return False, "Safe"

    @staticmethod
    def is_generated_path(relative_path: str) -> Tuple[bool, str]:
        """Check if path is located in a generated/build/cache folder."""
        normalized = relative_path.replace("\\", "/").strip("/")
        parts = normalized.split("/")
        
        for part in parts:
            if part in GENERATED_DIRS:
                return True, f"Path is inside a protected generated/build directory: '{part}'"
        return False, "Not generated"

    @staticmethod
    def is_binary_path(relative_path: str) -> Tuple[bool, str]:
        """Check if path has a binary file extension."""
        _, ext = os.path.splitext(relative_path.lower())
        if ext in BINARY_EXTENSIONS:
            return True, f"Binary file extension '{ext}' is blocked from modification"
        return False, "Text"

    @staticmethod
    def scan_for_secrets(content: Optional[str]) -> Tuple[bool, str]:
        """
        Defensive scan of proposed patch content for credentials/keys.
        Does not reveal the secret value if detected.
        """
        if not content:
            return False, "Clean"

        for pattern in SECRET_CONTENT_PATTERNS:
            if pattern.search(content):
                return True, "Potential high-confidence secret or credential detected in patch content."

        return False, "Clean"
