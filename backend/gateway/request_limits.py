"""
Phase 2H — Request Size & Complexity Limits
Validates payload byte lengths, JSON nesting depth, string lengths, array lengths, and object field counts.
"""
from __future__ import annotations
from typing import Any, Dict, List
from config.settings import config
from gateway.errors import GatewayError, REQUEST_TOO_LARGE, INVALID_REQUEST


def validate_payload_size(byte_count: int):
    """Validates raw payload byte size against global bounds."""
    if byte_count > config.max_request_bytes:
        raise GatewayError(
            code=REQUEST_TOO_LARGE,
            detail=f"Request size {byte_count} exceeds maximum allowed {config.max_request_bytes} bytes.",
            status_code=413,
        )


def validate_json_structure(data: Any, current_depth: int = 1):
    """
    Recursively inspects parsed JSON data to enforce depth, length, and field bounds.
    """
    if current_depth > config.max_json_depth:
        raise GatewayError(
            code=INVALID_REQUEST,
            detail=f"JSON nesting depth exceeds limit of {config.max_json_depth}.",
            status_code=400,
        )

    if isinstance(data, dict):
        if len(data) > config.max_object_fields:
            raise GatewayError(
                code=INVALID_REQUEST,
                detail=f"JSON object exceeds limit of {config.max_object_fields} keys.",
                status_code=400,
            )
        for k, v in data.items():
            if isinstance(k, str) and len(k) > config.max_string_length:
                raise GatewayError(
                    code=INVALID_REQUEST,
                    detail="JSON key length exceeds maximum allowed length.",
                    status_code=400,
                )
            validate_json_structure(v, current_depth + 1)

    elif isinstance(data, list):
        if len(data) > config.max_array_length:
            raise GatewayError(
                code=INVALID_REQUEST,
                detail=f"JSON array length exceeds limit of {config.max_array_length} items.",
                status_code=400,
            )
        for item in data:
            validate_json_structure(item, current_depth + 1)

    elif isinstance(data, str):
        if len(data) > config.max_string_length:
            raise GatewayError(
                code=INVALID_REQUEST,
                detail="JSON string value exceeds maximum allowed length.",
                status_code=400,
            )
