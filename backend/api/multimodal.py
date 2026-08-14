"""
Phase 2I.1 — Multimodal Capability API Router
Exposes secure REST endpoints for file, document, image analysis, OCR, and creative generation.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status

from multimodal.schemas import (
    MultimodalRequest,
    MultimodalResult,
    MultimodalOperation,
    MultimodalStatus,
)
from multimodal.errors import (
    MultimodalError,
    AUTH_REQUIRED,
    WORKSPACE_NOT_AUTHORIZED,
    TENANT_NOT_AUTHORIZED,
    INVALID_REQUEST,
    EMPTY_REQUEST,
    UNSUPPORTED_FILE_TYPE,
    FILE_NOT_FOUND,
    FILE_TOO_LARGE,
    DOCUMENT_TOO_LARGE,
    IMAGE_TOO_LARGE,
    OCR_TOO_LARGE,
    TOO_MANY_FILES,
    SENSITIVE_FILE_BLOCKED,
    SECRET_DETECTED,
    PATH_TRAVERSAL_DETECTED,
    PROMPT_INJECTION_DETECTED,
    PERMISSION_DENIED,
    FORBIDDEN_PERMISSION_LEVEL,
    CAPABILITY_UNAVAILABLE,
    PROVIDER_ERROR,
    RESOURCE_NOT_FOUND,
    RATE_LIMIT_EXCEEDED,
    OPERATION_CANCELLED,
    STORE_ERROR,
)
from multimodal.orchestrator import MultimodalOrchestrator
from api.auth import get_auth_context
from auth.schemas import AuthenticationContext
from utils.logger import logger

multimodal_router = APIRouter(prefix="/api/multimodal", tags=["multimodal"])
_orchestrator = MultimodalOrchestrator()


def _handle_multimodal_error(e: MultimodalError):
    if e.code == AUTH_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    if e.code in (WORKSPACE_NOT_AUTHORIZED, TENANT_NOT_AUTHORIZED, FORBIDDEN_PERMISSION_LEVEL, SENSITIVE_FILE_BLOCKED, PATH_TRAVERSAL_DETECTED):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    if e.code in (RESOURCE_NOT_FOUND, FILE_NOT_FOUND):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    if e.code in (FILE_TOO_LARGE, DOCUMENT_TOO_LARGE, IMAGE_TOO_LARGE, OCR_TOO_LARGE, TOO_MANY_FILES):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    if e.code == CAPABILITY_UNAVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": e.code, "message": e.message, "details": e.details}
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": e.code, "message": e.message, "details": e.details}
    )


@multimodal_router.post("/analyze", response_model=MultimodalResult)
def analyze_file(
    body: MultimodalRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Analyzes a workspace text or source code file."""
    try:
        body.operation = MultimodalOperation.FILE_ANALYSIS
        return _orchestrator.execute(
            request=body,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.post("/document/analyze", response_model=MultimodalResult)
def analyze_document(
    body: MultimodalRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Analyzes a PDF, DOCX, or structured document."""
    try:
        body.operation = MultimodalOperation.DOCUMENT_ANALYSIS
        return _orchestrator.execute(
            request=body,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.post("/image/analyze", response_model=MultimodalResult)
def analyze_image(
    body: MultimodalRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Analyzes a screenshot, diagram, or UI asset."""
    try:
        body.operation = MultimodalOperation.IMAGE_ANALYSIS
        return _orchestrator.execute(
            request=body,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.post("/ocr", response_model=MultimodalResult)
def extract_ocr(
    body: MultimodalRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Performs OCR text extraction on an image."""
    try:
        body.operation = MultimodalOperation.OCR
        return _orchestrator.execute(
            request=body,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.post("/image/generate", response_model=MultimodalResult)
def generate_image(
    body: MultimodalRequest,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Generates an image artifact or design mockup specification."""
    try:
        if body.options.get("design_type"):
            body.operation = MultimodalOperation.DESIGN_GENERATION
        else:
            body.operation = MultimodalOperation.IMAGE_GENERATION
        return _orchestrator.execute(
            request=body,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.get("/{request_id}", response_model=MultimodalResult)
def get_multimodal_result(
    request_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Retrieves a multimodal operation result by request ID."""
    try:
        return _orchestrator.get_result(request_id, context.tenant_id)
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.get("/{request_id}/status", response_model=Dict[str, Any])
def get_multimodal_status(
    request_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Queries the status and findings summary of a multimodal request."""
    try:
        res = _orchestrator.get_result(request_id, context.tenant_id)
        return {
            "status": "ok",
            "request_id": res.request_id,
            "operation": res.operation,
            "execution_status": res.status,
            "warnings": res.warnings,
            "duration_ms": res.duration_ms,
        }
    except MultimodalError as e:
        _handle_multimodal_error(e)


@multimodal_router.post("/{request_id}/cancel", response_model=Dict[str, Any])
def cancel_multimodal_request(
    request_id: str,
    context: AuthenticationContext = Depends(get_auth_context),
):
    """Cancels a pending or running multimodal request."""
    try:
        success = _orchestrator.cancel_request(request_id, context.tenant_id)
        return {
            "status": "ok",
            "request_id": request_id,
            "cancelled": success,
        }
    except MultimodalError as e:
        _handle_multimodal_error(e)
