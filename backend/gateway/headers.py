"""
Phase 2H — Gateway Security Headers & Request Correlation
Sanitizes request IDs and injects standard security response headers.
"""
from __future__ import annotations
import re
import uuid
from typing import Dict, Optional
from config.settings import config

MAX_REQUEST_ID_LEN = 64
REQ_ID_CLEAN_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def sanitize_or_generate_request_id(client_req_id: Optional[str]) -> str:
    """
    Validates and sanitizes client-supplied X-Request-ID, generating a secure one if absent or invalid.
    Prevents newline, control character injection, and bounded length.
    """
    if not client_req_id:
        return f"req_{uuid.uuid4().hex[:12]}"
    
    clean = client_req_id.strip()
    if len(clean) > MAX_REQUEST_ID_LEN or not REQ_ID_CLEAN_RE.match(clean):
        return f"req_{uuid.uuid4().hex[:12]}"
    
    return clean


def get_security_headers() -> Dict[str, str]:
    """
    Returns standard production-hardened security response headers.
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "X-XSS-Protection": "1; mode=block",
    }
    
    if config.is_production() and config.enable_hsts:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
    return headers
