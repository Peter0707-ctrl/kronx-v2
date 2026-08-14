"""
Phase 2H — Centralized Production & Gateway Configuration
Provides validated configuration settings with environment-aware safe defaults.
"""
from __future__ import annotations
import os
from typing import List
from pydantic import BaseModel, Field


class GatewayConfig(BaseModel):
    environment: str = Field(default_factory=lambda: os.getenv("KRONX_ENV", "development").lower())
    
    # Request limits
    max_request_bytes: int = 10 * 1024 * 1024  # 10 MB
    max_json_depth: int = 20
    max_string_length: int = 500_000
    max_array_length: int = 2000
    max_object_fields: int = 500
    
    # Concurrency limits
    max_concurrent_scans: int = 5
    max_concurrent_plans: int = 10
    max_concurrent_executions: int = 5
    max_concurrent_modifications: int = 5
    max_concurrent_verifications: int = 5
    
    # Rate limits (sliding window)
    rate_limit_window_seconds: int = 60
    rate_limit_requests_per_window: int = 120
    
    # Specific operation limits per minute
    limit_auth_failures_per_window: int = 5
    limit_scans_per_window: int = 15
    limit_plans_per_window: int = 20
    limit_executions_per_window: int = 10
    limit_modifications_per_window: int = 15
    limit_verifications_per_window: int = 15
    
    # Tenant quotas
    max_tenant_workspaces: int = 50
    max_tenant_sessions: int = 20
    max_tenant_concurrent_jobs: int = 10
    max_tenant_stored_plans: int = 200
    max_tenant_stored_executions: int = 200
    max_tenant_stored_modifications: int = 200
    max_tenant_stored_verifications: int = 200
    
    # CORS
    cors_allowed_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://kronx.ai",
    ]
    
    # Security headers
    enable_hsts: bool = False  # Enabled in production HTTPS

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_testing(self) -> bool:
        return self.environment == "testing"


config = GatewayConfig()
