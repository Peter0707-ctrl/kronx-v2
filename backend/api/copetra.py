"""
Phase 5 — Copetra Universal Task API Router
Exposes unified, authenticated, tenant-isolated endpoints for Copetra Master Agent:
- POST /api/copetra/task: Primary Universal Multimodal Execution
- GET /api/copetra/artifacts/{artifact_id}: Secure Artifact Retrieval & Downloads
- GET /api/copetra/capabilities: Registered Internal Capabilities
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, Response
from fastapi.responses import Response as FastAPIResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from auth.schemas import AuthenticationContext, UserRole
from intelligence.schemas import AttachmentPayload
from intelligence.master_agent import CopetraMasterAgent
from intelligence.artifacts import ArtifactRegistry

copetra_router = APIRouter(prefix="/api/copetra", tags=["Copetra Universal Agent"])
_master_agent = CopetraMasterAgent()
_artifact_registry = ArtifactRegistry()


class UniversalTaskRequest(BaseModel):
    message: str = Field(..., description="User question, prompt, instruction, or task")
    attachments: Optional[List[AttachmentPayload]] = Field(default_factory=list, description="Attached documents or images")
    conversation_id: Optional[str] = Field("default", description="Conversation context ID")
    mode: Optional[str] = Field("Universal", description="Reasoning mode hint (Academic, Developer, etc.)")
    language: Optional[str] = Field("auto", description="Preferred response language (sw, en, auto)")
    detail_level: Optional[str] = Field("DETAILED", description="Desired response depth (CONCISE, DETAILED, STEP_BY_STEP)")


def _get_auth_context(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> AuthenticationContext:
    """Builds authoritative context for Copetra Universal Agent."""
    if hasattr(request.state, "auth_context") and request.state.auth_context:
        return request.state.auth_context

    t_id = x_tenant_id or "tenant_default"
    u_id = x_user_id or "user_default"
    role_val = UserRole.USER
    if x_role and x_role.upper() in [r.value for r in UserRole]:
        role_val = UserRole(x_role.upper())

    return AuthenticationContext(
        request_id=x_request_id or "req_copetra",
        session_id="sess_copetra",
        user_id=u_id,
        tenant_id=t_id,
        role=role_val,
    )


@copetra_router.post("/task")
async def execute_task(
    payload: UniversalTaskRequest,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """
    Executes any universal request through the unified Copetra Master Agent.
    Handles Text, Document Analysis, Vision, Math, Code, Diagrams, and Document Generation.
    """
    try:
        result = _master_agent.process_task(
            context=context,
            message=payload.message,
            attachments=payload.attachments,
            conversation_id=payload.conversation_id or "default",
            mode=payload.mode or "Universal",
            language=payload.language or "auto",
            detail_level=payload.detail_level or "DETAILED"
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INTERNAL_ERROR", "message": f"Task execution error: {str(e)}"}
        )


@copetra_router.get("/artifacts/{artifact_id}")
async def download_artifact(
    artifact_id: str,
    context: AuthenticationContext = Depends(_get_auth_context),
):
    """Securely downloads a generated file artifact (Word, Excel, PowerPoint, PDF, Diagram)."""
    res = _artifact_registry.get_artifact(artifact_id, tenant_id=context.tenant_id)
    if not res:
        raise HTTPException(status_code=404, detail={"code": "ARTIFACT_NOT_FOUND", "message": f"Artifact '{artifact_id}' not found."})

    artifact, file_bytes = res
    headers = {
        "Content-Disposition": f'attachment; filename="{artifact.filename}"',
        "X-Artifact-ID": artifact.artifact_id,
        "X-Artifact-SHA256": artifact.sha256,
    }
    return FastAPIResponse(content=file_bytes, media_type=artifact.mime_type, headers=headers)


@copetra_router.get("/capabilities")
async def list_capabilities():
    """Lists registered internal capability engines in the Copetra Master Agent."""
    return {
        "agent": "Copetra AI Master Agent",
        "capabilities": [
            "REASONING_ENGINE",
            "ACADEMIC_ENGINE",
            "VISION_OCR",
            "DOCUMENT_PARSER",
            "MATH_ENGINE",
            "CODE_AST_ENGINE",
            "DATA_ANALYSIS",
            "GENERATOR_DOCX",
            "GENERATOR_PDF",
            "GENERATOR_XLSX",
            "GENERATOR_PPTX",
            "GENERATOR_CSV",
            "GENERATOR_JSON",
            "GENERATOR_DIAGRAM",
            "QUALITY_GATE_15_POINT",
            "CLAIM_VERIFICATION"
        ],
        "supported_input_formats": ["PDF", "DOCX", "XLSX", "PPTX", "CSV", "TSV", "JSON", "XML", "HTML", "TXT", "MD", "PY", "JS", "TS", "PNG", "JPG", "WEBP"],
        "supported_output_formats": ["DOCX", "PDF", "XLSX", "PPTX", "CSV", "JSON", "TXT", "MD", "SVG", "MERMAID"]
    }
