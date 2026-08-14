"""
Phase 2I.1 — Multimodal Intelligence & Creative Capability Module Exports
"""
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
from multimodal.schemas import (
    MultimodalOperation,
    MultimodalStatus,
    RiskLevel,
    DocumentSection,
    DocumentTable,
    FileAnalysisResult,
    DocumentAnalysisResult,
    ImageAnalysisResult,
    OCRResult,
    ImageGenerationRequest,
    ImageGenerationResult,
    DesignGenerationRequest,
    DesignGenerationResult,
    MultimodalRequest,
    MultimodalResult,
)
from multimodal.file_types import (
    FileCategory,
    classify_file_type,
    is_sensitive_filename,
    is_blocked_binary,
)
from multimodal.limits import (
    MAX_UPLOAD_BYTES,
    MAX_DOCUMENT_TEXT_BYTES,
    MAX_IMAGE_BYTES,
    MAX_IMAGE_DIMENSION,
    MAX_OCR_TEXT_BYTES,
    MAX_FILES_PER_REQUEST,
    MAX_MULTIMODAL_CONTEXT_ITEMS,
    check_file_size,
    check_document_text_size,
    check_image_size,
    check_ocr_text_size,
    check_file_count,
)
from multimodal.sanitizer import (
    redact_secrets,
    detect_prompt_injection,
    sanitize_log_message,
)
from multimodal.policy import MultimodalPolicyEngine
from multimodal.providers import (
    MultimodalProvider,
    MockMultimodalProvider,
    ProviderRegistry,
)
from multimodal.file_analyzer import FileAnalyzer
from multimodal.document_analyzer import DocumentAnalyzer
from multimodal.image_analyzer import ImageAnalyzer
from multimodal.ocr import OCREngine
from multimodal.generation import CreativeGenerationEngine
from multimodal.context import MultimodalContextIntegrator
from multimodal.audit import log_multimodal_audit
from multimodal.store import MultimodalStore
from multimodal.orchestrator import MultimodalOrchestrator

__all__ = [
    "MultimodalError",
    "MultimodalOperation",
    "MultimodalStatus",
    "RiskLevel",
    "DocumentSection",
    "DocumentTable",
    "FileAnalysisResult",
    "DocumentAnalysisResult",
    "ImageAnalysisResult",
    "OCRResult",
    "ImageGenerationRequest",
    "ImageGenerationResult",
    "DesignGenerationRequest",
    "DesignGenerationResult",
    "MultimodalRequest",
    "MultimodalResult",
    "FileCategory",
    "classify_file_type",
    "is_sensitive_filename",
    "is_blocked_binary",
    "check_file_size",
    "check_document_text_size",
    "check_image_size",
    "check_ocr_text_size",
    "check_file_count",
    "redact_secrets",
    "detect_prompt_injection",
    "sanitize_log_message",
    "MultimodalPolicyEngine",
    "MultimodalProvider",
    "MockMultimodalProvider",
    "ProviderRegistry",
    "FileAnalyzer",
    "DocumentAnalyzer",
    "ImageAnalyzer",
    "OCREngine",
    "CreativeGenerationEngine",
    "MultimodalContextIntegrator",
    "log_multimodal_audit",
    "MultimodalStore",
    "MultimodalOrchestrator",
]
