"""
Phase 2G — Cryptographic Token Generator & Validator
Generates secure random bearer tokens and constant-time hash comparisons.
Never logs raw tokens.
"""
from __future__ import annotations
import hashlib
import secrets


def generate_session_token() -> str:
    """Generates a high-entropy cryptographically secure random session token."""
    return f"kx_{secrets.token_urlsafe(32)}"


def hash_token(raw_token: str) -> str:
    """Computes SHA256 hex digest of raw token for safe persistence."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def verify_token(raw_token: str, expected_token_hash: str) -> bool:
    """Verifies raw token against stored hash using constant-time comparison."""
    if not raw_token or not expected_token_hash:
        return False
    computed_hash = hash_token(raw_token)
    return secrets.compare_digest(computed_hash, expected_token_hash)
