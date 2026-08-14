"""
Phase 2I.1 — Multimodal Capability Orchestrator
Master coordinator for safe multimodal vision, OCR, document, and creative generation operations.
"""
import time
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from workspace.store import WorkspaceStore
from multimodal.schemas import (
    MultimodalRequest,
    MultimodalResult,
    MultimodalOperation,
    MultimodalStatus,
    ImageGenerationRequest,
    DesignGenerationRequest,
    FileAnalysisResult,
    DocumentAnalysisResult,
    ImageAnalysisResult,
    OCRResult,
    ImageGenerationResult,
    DesignGenerationResult,
)
from multimodal.errors import (
    MultimodalError,
    INVALID_REQUEST,
    EMPTY_REQUEST,
    RESOURCE_NOT_FOUND,
    OPERATION_CANCELLED,
    WORKSPACE_NOT_AUTHORIZED,
)
from multimodal.policy import MultimodalPolicyEngine
from multimodal.file_analyzer import FileAnalyzer
from multimodal.document_analyzer import DocumentAnalyzer
from multimodal.image_analyzer import ImageAnalyzer
from multimodal.ocr import OCREngine
from multimodal.generation import CreativeGenerationEngine
from multimodal.context import MultimodalContextIntegrator
from multimodal.store import MultimodalStore
from multimodal.audit import log_multimodal_audit
from utils.logger import logger


class MultimodalOrchestrator:
    """Coordinates multimodal analysis, creative synthesis, policy enforcement, and audit."""

    def __init__(
        self,
        workspace_store: Optional[WorkspaceStore] = None,
        store: Optional[MultimodalStore] = None,
        policy_engine: Optional[MultimodalPolicyEngine] = None,
    ):
        self._workspace_store = workspace_store or WorkspaceStore()
        self._store = store or MultimodalStore()
        self._policy_engine = policy_engine or MultimodalPolicyEngine()

        self._file_analyzer = FileAnalyzer(self._workspace_store)
        self._doc_analyzer = DocumentAnalyzer(self._workspace_store)
        self._img_analyzer = ImageAnalyzer(self._workspace_store)
        self._ocr_engine = OCREngine()
        self._generation_engine = CreativeGenerationEngine()
        self._context_integrator = MultimodalContextIntegrator()

        self._cancelled_requests = set()

    def execute(
        self,
        request: MultimodalRequest,
        tenant_id: str,
        user_id: str,
    ) -> MultimodalResult:
        """
        Executes a multimodal operation within authorized multi-tenant and workspace boundaries.
        """
        t0 = time.perf_counter()
        req_id = request.request_id

        if not request.workspace_id:
            raise MultimodalError(INVALID_REQUEST, "workspace_id is required.")

        # 1. Authorize Workspace
        ws_data = self._workspace_store.get_workspace(request.workspace_id)
        if not ws_data or ws_data.get("status") != "authorized":
            log_multimodal_audit(
                request_id=req_id,
                tenant_id=tenant_id,
                workspace_id=request.workspace_id,
                operation=request.operation.value,
                status="FAILED",
                agent_id=request.agent_id,
                duration_ms=(time.perf_counter() - t0) * 1000,
                error_code=WORKSPACE_NOT_AUTHORIZED,
            )
            raise MultimodalError(WORKSPACE_NOT_AUTHORIZED, f"Workspace '{request.workspace_id}' is not authorized.")

        # 2. Evaluate Policy
        self._policy_engine.evaluate_request(
            operation=request.operation,
            workspace_authorized=True,
            requested_permission="READ",
        )

        file_res: Optional[FileAnalysisResult] = None
        doc_res: Optional[DocumentAnalysisResult] = None
        img_res: Optional[ImageAnalysisResult] = None
        ocr_res: Optional[OCRResult] = None
        gen_res: Optional[ImageGenerationResult] = None
        des_res: Optional[DesignGenerationResult] = None
        warnings: List[str] = []
        result_size: int = 0
        input_type: str = ""

        try:
            # 3. Check for early cancellation
            if req_id in self._cancelled_requests:
                raise MultimodalError(OPERATION_CANCELLED, f"Request '{req_id}' was cancelled.")

            # 4. Dispatch Operation
            if request.operation == MultimodalOperation.FILE_ANALYSIS:
                input_type = "workspace_file"
                if not request.file_reference:
                    raise MultimodalError(INVALID_REQUEST, "file_reference required for FILE_ANALYSIS.")
                file_res = self._file_analyzer.analyze_workspace_file(
                    workspace_id=request.workspace_id,
                    relative_path=request.file_reference,
                )
                warnings.extend(file_res.warnings)
                result_size = file_res.size_bytes

            elif request.operation == MultimodalOperation.DOCUMENT_ANALYSIS:
                input_type = "document"
                if request.file_reference:
                    doc_res = self._doc_analyzer.analyze_document_file(
                        workspace_id=request.workspace_id,
                        relative_path=request.file_reference,
                    )
                elif request.raw_content:
                    doc_bytes = base64.b64decode(request.raw_content)
                    doc_res = self._doc_analyzer.analyze_document_bytes(
                        doc_bytes=doc_bytes,
                        filename=request.filename or "document.pdf",
                        mime_type=request.mime_type,
                    )
                else:
                    raise MultimodalError(INVALID_REQUEST, "file_reference or raw_content required for DOCUMENT_ANALYSIS.")
                warnings.extend(doc_res.warnings)
                result_size = len(doc_res.text_preview)

            elif request.operation == MultimodalOperation.IMAGE_ANALYSIS:
                input_type = "image"
                if request.file_reference:
                    img_res = self._img_analyzer.analyze_workspace_image(
                        workspace_id=request.workspace_id,
                        relative_path=request.file_reference,
                        prompt=request.prompt,
                    )
                elif request.raw_content:
                    img_bytes = base64.b64decode(request.raw_content)
                    img_res = self._img_analyzer.analyze_image_bytes(
                        image_bytes=img_bytes,
                        mime_type=request.mime_type or "image/png",
                        prompt=request.prompt or "Analyze this image.",
                    )
                else:
                    raise MultimodalError(INVALID_REQUEST, "file_reference or raw_content required for IMAGE_ANALYSIS.")
                warnings.extend(img_res.warnings)
                result_size = len(img_res.description)

            elif request.operation == MultimodalOperation.OCR:
                input_type = "ocr_image"
                if request.raw_content:
                    img_bytes = base64.b64decode(request.raw_content)
                elif request.file_reference:
                    ws_root = ws_data.get("root_path")
                    safe_path = self._file_analyzer._workspace_store.get_workspace(request.workspace_id)
                    from tools.path_verify import verify_safe_path
                    import os
                    safe_file = verify_safe_path(ws_root, request.file_reference)

                    with open(safe_file, "rb") as f:
                        img_bytes = f.read()
                else:
                    raise MultimodalError(INVALID_REQUEST, "file_reference or raw_content required for OCR.")
                ocr_res = self._ocr_engine.extract_text_from_image_bytes(
                    image_bytes=img_bytes,
                    mime_type=request.mime_type or "image/png",
                )
                warnings.extend(ocr_res.warnings)
                result_size = len(ocr_res.extracted_text)

            elif request.operation == MultimodalOperation.IMAGE_GENERATION:
                input_type = "generation_prompt"
                if not request.prompt:
                    raise MultimodalError(EMPTY_REQUEST, "prompt required for IMAGE_GENERATION.")
                gen_req = ImageGenerationRequest(
                    prompt=request.prompt,
                    style=request.options.get("style", "modern"),
                    aspect_ratio=request.options.get("aspect_ratio", "1:1"),
                    width=request.options.get("width", 1024),
                    height=request.options.get("height", 1024),
                    category=request.options.get("category", "general"),
                )
                gen_res = self._generation_engine.generate_image(gen_req)
                warnings.extend(gen_res.warnings)
                result_size = len(gen_res.b64_data or "")

            elif request.operation == MultimodalOperation.DESIGN_GENERATION:
                input_type = "design_spec"
                des_req = DesignGenerationRequest(
                    title=request.filename or "System Design",
                    design_type=request.options.get("design_type", "ui_mockup"),
                    prompt=request.prompt or "Create modern clean interface mockup.",
                    style_system=request.options.get("style_system", "modern_clean"),
                    components=request.options.get("components", []),
                    color_palette=request.options.get("color_palette", []),
                )
                des_res = self._generation_engine.generate_design(des_req)
                warnings.extend(des_res.warnings)
                result_size = len(str(des_res.structured_design))

            # 5. Integrate Context Findings
            facts, inferences, assumptions = self._context_integrator.integrate_findings(
                file_res=file_res,
                doc_res=doc_res,
                img_res=img_res,
                ocr_res=ocr_res,
                gen_res=gen_res,
                des_res=des_res,
            )

            duration_ms = (time.perf_counter() - t0) * 1000

            result = MultimodalResult(
                request_id=req_id,
                tenant_id=tenant_id,
                user_id=user_id,
                workspace_id=request.workspace_id,
                operation=request.operation,
                status=MultimodalStatus.COMPLETED,
                file_analysis=file_res,
                document_analysis=doc_res,
                image_analysis=img_res,
                ocr_result=ocr_res,
                generation_result=gen_res,
                design_result=des_res,
                facts=facts,
                inferences=inferences,
                assumptions=assumptions,
                warnings=list(dict.fromkeys(warnings)),
                duration_ms=round(duration_ms, 2),
            )

            # 6. Persist & Audit
            self._store.save_result(result)

            log_multimodal_audit(
                request_id=req_id,
                tenant_id=tenant_id,
                workspace_id=request.workspace_id,
                operation=request.operation.value,
                status="COMPLETED",
                agent_id=request.agent_id,
                duration_ms=duration_ms,
                input_type=input_type,
                provider_type="mock",
                result_size=result_size,
                risk_level="HIGH" if warnings else "LOW",
            )

            return result

        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000
            err_code = getattr(e, "code", "EXECUTION_ERROR")
            log_multimodal_audit(
                request_id=req_id,
                tenant_id=tenant_id,
                workspace_id=request.workspace_id,
                operation=request.operation.value,
                status="FAILED",
                agent_id=request.agent_id,
                duration_ms=duration_ms,
                input_type=input_type,
                error_code=err_code,
            )
            if isinstance(e, MultimodalError):
                raise
            raise MultimodalError(err_code, str(e))

    def get_result(self, request_id: str, tenant_id: str) -> Optional[MultimodalResult]:
        """Retrieves a result under strict tenant isolation."""
        res = self._store.get_result(request_id, tenant_id)
        if not res:
            raise MultimodalError(RESOURCE_NOT_FOUND, f"Multimodal result '{request_id}' not found.")
        return res

    def cancel_request(self, request_id: str, tenant_id: str) -> bool:
        """Cancels a pending or processing multimodal request."""
        self._cancelled_requests.add(request_id)
        return self._store.update_status(request_id, tenant_id, MultimodalStatus.CANCELLED)
