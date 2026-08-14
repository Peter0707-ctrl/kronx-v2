"""
Phase 2G — Password Security & Hashing
Implements standard-library PBKDF2-HMAC-SHA256 with 100,000 iterations and constant-time comparisons.
Never stores or logs plaintext passwords.
"""
from __future__ import annotations
import hashlib
import os
import secrets
from typing import Tuple

PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


class PasswordManager:
    """Provides secure password hashing and constant-time validation."""

    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """
        Generates a cryptographic salt and hashes the password with PBKDF2-HMAC-SHA256.
        Returns: (password_hash_hex, salt_hex)
        """
        salt = secrets.token_bytes(SALT_BYTES)
        derived_key = hashlib.pbkdf2_hmac(
            hash_name="sha256",
            password=password.encode("utf-8"),
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return derived_key.hex(), salt.hex()

    @staticmethod
    def verify_password(password: str, expected_hash_hex: str, salt_hex: str) -> bool:
        """
        Verifies a plaintext password against expected hash and salt using constant-time comparison.
        """
        try:
            salt = bytes.fromhex(salt_hex)
            derived_key = hashlib.pbkdf2_hmac(
                hash_name="sha256",
                password=password.encode("utf-8"),
                salt=salt,
                iterations=PBKDF2_ITERATIONS,
            )
            return secrets.compare_digest(derived_key.hex(), expected_hash_hex)
        except Exception:
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """Validates basic password security constraints."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if len(password) > 128:
            return False, "Password cannot exceed 128 characters."
        return True, ""
