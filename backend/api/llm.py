"""
Phase 2J — LLM Gateway REST API Router
Exposes model inference, streaming, routing, and provider health endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional, List

from auth.schemas import AuthenticationContext
from api.auth import get_auth_context
from auth.authorization import MultiTenantAuthorizer

from llm.schemas import (
    LLMRequest,
    LLMResponse,
    LLMInferenceRecord,
    LLMProvider,
)
from llm.orchestrator import LLMOrchestrator
from llm.capabilities import ModelCapabilityRegistry
from llm.providers import ProviderRegistry
from llm.health import LLMHealthChecker
from llm.errors import (
    LLMError,
    UNAUTHORIZED,
    FORBIDDEN,
    MODEL_NOT_FOUND,
    CAPABILITY_UNSUPPORTED,
    BUDGET_EXCEEDED,
    QUOTA_EXCEEDED,
    MODEL_OUTPUT_BLOCKED,
    PROMPT_INJECTION_DETECTED,
    FORBIDDEN_PERMISSION_LEVEL,
    RESOURCE_NOT_FOUND,
)

llm_router = APIRouter(prefix="/api/llm", tags=["llm"])

# Default singleton components
_model_registry = ModelCapabilityRegistry()
_provider_registry = ProviderRegistry()
_orchestrator = LLMOrchestrator(
    model_registry=_model_registry,
    provider_registry=_provider_registry,
)
_health_checker = LLMHealthChecker(_provider_registry, _model_registry)
_authorizer = MultiTenantAuthorizer()


from auth.errors import (
    AuthError,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    AUTHENTICATION_REQUIRED,
    RESOURCE_NOT_FOUND as AUTH_RESOURCE_NOT_FOUND,
)


@llm_router.post("/infer", response_model=LLMResponse)
def infer(
    request_body: LLMRequest,
    auth_ctx: Optional[AuthenticationContext] = Depends(get_auth_context),
):
    """Executes validated non-streaming model completion."""
    try:
        # Enforce authenticated tenant context if present
        if auth_ctx:
            request_body.tenant_id = auth_ctx.tenant_id
            request_body.user_id = auth_ctx.user_id

        # Workspace authorization if workspace_id specified
        if request_body.workspace_id and auth_ctx:
            _authorizer.authorize_workspace_access(auth_ctx, request_body.workspace_id)

        return _orchestrator.execute(request_body, is_authenticated=True)

    except AuthError as ae:
        status_code = 403
        if ae.code == AUTHENTICATION_REQUIRED:
            status_code = 401
        elif ae.code in [WORKSPACE_NOT_AUTHORIZED, AUTH_RESOURCE_NOT_FOUND]:
            status_code = 404
        raise HTTPException(
            status_code=status_code,
            detail={"code": ae.code, "message": ae.detail},
        )
    except LLMError as e:
        status_code = 400
        if e.code == UNAUTHORIZED:
            status_code = 401
        elif e.code in [FORBIDDEN, FORBIDDEN_PERMISSION_LEVEL, MODEL_OUTPUT_BLOCKED]:
            status_code = 403
        elif e.code in [MODEL_NOT_FOUND, RESOURCE_NOT_FOUND]:
            status_code = 404
        elif e.code in [BUDGET_EXCEEDED, QUOTA_EXCEEDED]:
            status_code = 429

        raise HTTPException(
            status_code=status_code,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred during inference."},
        )


@llm_router.post("/stream")
def stream_infer(
    request_body: LLMRequest,
    auth_ctx: Optional[AuthenticationContext] = Depends(get_auth_context),
):
    """Executes bounded streaming model completion."""
    try:
        if auth_ctx:
            request_body.tenant_id = auth_ctx.tenant_id
            request_body.user_id = auth_ctx.user_id

        if request_body.workspace_id and auth_ctx:
            _authorizer.authorize_workspace_access(auth_ctx, request_body.workspace_id)

        stream_gen = _orchestrator.stream(request_body, is_authenticated=True)

        return StreamingResponse(stream_gen, media_type="text/plain")

    except AuthError as ae:
        status_code = 403
        if ae.code == AUTHENTICATION_REQUIRED:
            status_code = 401
        elif ae.code in [WORKSPACE_NOT_AUTHORIZED, AUTH_RESOURCE_NOT_FOUND]:
            status_code = 404
        raise HTTPException(
            status_code=status_code,
            detail={"code": ae.code, "message": ae.detail},
        )
    except LLMError as e:
        status_code = 400
        if e.code == UNAUTHORIZED:
            status_code = 401
        elif e.code in [FORBIDDEN, FORBIDDEN_PERMISSION_LEVEL, MODEL_OUTPUT_BLOCKED]:
            status_code = 403
        elif e.code in [BUDGET_EXCEEDED, QUOTA_EXCEEDED]:
            status_code = 429

        raise HTTPException(
            status_code=status_code,
            detail={"code": e.code, "message": e.message, "details": e.details},
        )



def _to_str(v) -> str:
    return v.value if hasattr(v, "value") else str(v)


@llm_router.get("/models")
def list_models(provider: Optional[str] = None):
    """Returns active models and capabilities without exposing internal credentials."""
    prov_enum = None
    if provider:
        try:
            prov_enum = LLMProvider(provider.upper())
        except Exception:
            pass
    models = _model_registry.list_models(prov_enum)
    return {
        "models": [
            {
                "id": m.id,
                "name": m.name,
                "provider": _to_str(m.provider),
                "capabilities": [_to_str(c) for c in m.capabilities],
                "max_context_tokens": m.max_context_tokens,
                "max_output_tokens": m.max_output_tokens,
            }
            for m in models
        ]
    }


@llm_router.get("/health")
def get_health():
    """Sanitized provider diagnostics."""
    return _health_checker.get_health_report()


@llm_router.get("/{request_id}", response_model=LLMInferenceRecord)
def get_inference_record(
    request_id: str,
    auth_ctx: Optional[AuthenticationContext] = Depends(get_auth_context),
):
    """Retrieves stored inference record strictly within caller tenant boundary."""
    tenant_id = auth_ctx.tenant_id if auth_ctx else "default_tenant"
    record = _orchestrator.store.get_record(request_id, tenant_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": RESOURCE_NOT_FOUND, "message": f"Inference record '{request_id}' not found."},
        )
    return record


@llm_router.get("/{request_id}/status")
def get_inference_status(
    request_id: str,
    auth_ctx: Optional[AuthenticationContext] = Depends(get_auth_context),
):
    """Retrieves status of request within tenant boundary."""
    tenant_id = auth_ctx.tenant_id if auth_ctx else "default_tenant"
    record = _orchestrator.store.get_record(request_id, tenant_id)
    if not record:
        return {"request_id": request_id, "status": "UNKNOWN"}
    return {
        "request_id": record.request_id,
        "status": _to_str(record.status),
        "duration_ms": record.duration_ms,
        "risk_level": _to_str(record.risk_level),
    }



@llm_router.post("/{request_id}/cancel")
def cancel_inference(
    request_id: str,
    auth_ctx: Optional[AuthenticationContext] = Depends(get_auth_context),
):
    """Cooperatively cancels an active inference request."""
    tenant_id = auth_ctx.tenant_id if auth_ctx else "default_tenant"
    _orchestrator.cancel_request(request_id, tenant_id)
    return {"status": "ok", "request_id": request_id, "cancelled": True}
