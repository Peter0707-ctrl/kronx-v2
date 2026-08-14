"""
Phase 2I.1 — Multimodal Intelligence & Creative Capability Schemas
Strict Pydantic models for multimodal requests, analysis results, generation artifacts, and status.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from multimodal.file_types import FileCategory


class MultimodalOperation(str, Enum):
    FILE_ANALYSIS     = "FILE_ANALYSIS"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    IMAGE_ANALYSIS    = "IMAGE_ANALYSIS"
    OCR               = "OCR"
    IMAGE_GENERATION  = "IMAGE_GENERATION"
    DESIGN_GENERATION = "DESIGN_GENERATION"


class MultimodalStatus(str, Enum):
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED  = "COMPLETED"
    FAILED     = "FAILED"
    CANCELLED  = "CANCELLED"
    BLOCKED    = "BLOCKED"


class RiskLevel(str, Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


# ------------------------------------------------------------------
# Structured Content Models
# ------------------------------------------------------------------

class DocumentSection(BaseModel):
    title:    str
    level:    int = 1
    content:  str
    page:     Optional[int] = None


class DocumentTable(BaseModel):
    headers: List[str] = Field(default_factory=list)
    rows:    List[List[str]] = Field(default_factory=list)


# ------------------------------------------------------------------
# Analysis Result Models
# ------------------------------------------------------------------

class FileAnalysisResult(BaseModel):
    file_path:          str
    file_type:          str
    category:           FileCategory
    size_bytes:         int
    line_count:         int
    summary:            str
    structured_data:    Dict[str, Any] = Field(default_factory=dict)
    facts:              List[str] = Field(default_factory=list)
    inferences:         List[str] = Field(default_factory=list)
    assumptions:        List[str] = Field(default_factory=list)
    sanitized_content:  Optional[str] = None
    warnings:           List[str] = Field(default_factory=list)
    risk_level:         RiskLevel = RiskLevel.LOW


class DocumentAnalysisResult(BaseModel):
    document_type:  str
    page_count:     int
    sections:       List[DocumentSection] = Field(default_factory=list)
    tables:         List[DocumentTable] = Field(default_factory=list)
    metadata:       Dict[str, Any] = Field(default_factory=dict)
    text_preview:   str
    word_count:     int
    facts:          List[str] = Field(default_factory=list)
    inferences:     List[str] = Field(default_factory=list)
    assumptions:    List[str] = Field(default_factory=list)
    warnings:       List[str] = Field(default_factory=list)
    risk_level:     RiskLevel = RiskLevel.LOW


class ImageAnalysisResult(BaseModel):
    image_type:      str
    dimensions:      Dict[str, int] = Field(default_factory=dict)
    description:     str
    ui_elements:     List[Dict[str, Any]] = Field(default_factory=list)
    diagram_nodes:   List[Dict[str, Any]] = Field(default_factory=list)
    visible_text:    str = ""
    visual_summary:  str = ""
    facts:           List[str] = Field(default_factory=list)
    inferences:      List[str] = Field(default_factory=list)
    assumptions:     List[str] = Field(default_factory=list)
    warnings:        List[str] = Field(default_factory=list)
    risk_level:      RiskLevel = RiskLevel.LOW


class OCRResult(BaseModel):
    extracted_text: str
    word_count:     int
    confidence:     float = 1.0
    blocks:         List[Dict[str, Any]] = Field(default_factory=list)
    warnings:       List[str] = Field(default_factory=list)
    risk_level:     RiskLevel = RiskLevel.LOW


# ------------------------------------------------------------------
# Creative Generation Models
# ------------------------------------------------------------------

class ImageGenerationRequest(BaseModel):
    prompt:          str
    style:           str = "modern"
    aspect_ratio:    str = "1:1"
    width:           int = 1024
    height:          int = 1024
    negative_prompt: Optional[str] = None
    category:        str = "general"


class ImageGenerationResult(BaseModel):
    artifact_id:     str
    format:          str = "png"
    prompt:          str
    description:     str
    media_type:      str = "image/png"
    b64_data:        Optional[str] = None
    artifact_url:    Optional[str] = None
    dimensions:      Dict[str, int] = Field(default_factory=dict)
    style:           str = "modern"
    category:        str = "general"
    status:          str = "GENERATED"
    warnings:        List[str] = Field(default_factory=list)


class DesignGenerationRequest(BaseModel):
    title:           str
    design_type:     str = "ui_mockup"  # "ui_mockup", "logo", "diagram", "poster"
    prompt:          str
    style_system:    Optional[str] = "modern_clean"
    components:      List[str] = Field(default_factory=list)
    color_palette:   List[str] = Field(default_factory=list)
    layout:          Optional[str] = "flex_column"


class DesignGenerationResult(BaseModel):
    design_id:          str
    title:              str
    design_type:        str
    structured_design:  Dict[str, Any] = Field(default_factory=dict)
    mockup_metadata:    Dict[str, Any] = Field(default_factory=dict)
    visual_components:  List[Dict[str, Any]] = Field(default_factory=list)
    warnings:           List[str] = Field(default_factory=list)


# ------------------------------------------------------------------
# Top-Level Multimodal Request & Result Models
# ------------------------------------------------------------------

class MultimodalRequest(BaseModel):
    request_id:      str = Field(default_factory=lambda: f"mmreq_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
    workspace_id:    str
    agent_id:        Optional[str] = None
    operation:       MultimodalOperation
    file_reference:  Optional[str] = None
    mime_type:       Optional[str] = None
    filename:        Optional[str] = None
    prompt:          Optional[str] = None
    raw_content:     Optional[str] = None  # Base64 or text payload
    requested_mode:  Optional[str] = "ANALYZE"
    conversation_id: Optional[str] = None
    options:         Dict[str, Any] = Field(default_factory=dict)


class MultimodalResult(BaseModel):
    request_id:         str
    tenant_id:          str
    user_id:            str
    workspace_id:       str
    operation:          MultimodalOperation
    status:             MultimodalStatus
    file_analysis:      Optional[FileAnalysisResult] = None
    document_analysis:  Optional[DocumentAnalysisResult] = None
    image_analysis:     Optional[ImageAnalysisResult] = None
    ocr_result:         Optional[OCRResult] = None
    generation_result:  Optional[ImageGenerationResult] = None
    design_result:      Optional[DesignGenerationResult] = None
    facts:              List[str] = Field(default_factory=list)
    inferences:         List[str] = Field(default_factory=list)
    assumptions:        List[str] = Field(default_factory=list)
    warnings:           List[str] = Field(default_factory=list)
    duration_ms:        float = 0.0
    created_at:         str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
