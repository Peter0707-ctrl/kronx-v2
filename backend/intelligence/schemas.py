"""
Phase 4.0 — Intelligence Schemas & Data Contracts
Defines strict Pydantic models for intent classification, task contracts, multimodal evidence,
claim verification, topic drift guards, and the unified Copetra Intelligence Orchestrator.
"""
from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    ACADEMIC = "ACADEMIC"
    RESEARCH = "RESEARCH"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    OCR = "OCR"
    MULTI_DOCUMENT_ANALYSIS = "MULTI_DOCUMENT_ANALYSIS"
    CODE_GENERATION = "CODE_GENERATION"
    CODE_DEBUGGING = "CODE_DEBUGGING"
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    SOFTWARE_ENGINEERING = "SOFTWARE_ENGINEERING"
    MATHEMATICS = "MATHEMATICS"
    SCIENCE = "SCIENCE"
    BUSINESS = "BUSINESS"
    FINANCE = "FINANCE"
    FOREX = "FOREX"
    LEGAL_INFORMATION = "LEGAL_INFORMATION"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    SUMMARIZATION = "SUMMARIZATION"
    TRANSLATION = "TRANSLATION"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    COMPARISON = "COMPARISON"
    CREATIVE_WRITING = "CREATIVE_WRITING"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    EXPLANATION = "EXPLANATION"
    TUTORING = "TUTORING"
    PLANNING = "PLANNING"
    SYSTEM_DIAGNOSTICS = "SYSTEM_DIAGNOSTICS"
    UI_DESIGN = "UI_DESIGN"
    SYSTEM_ASSISTANCE = "SYSTEM_ASSISTANCE"
    GENERAL_QA = "GENERAL_QA"
    WRITING = "WRITING"
    EDITING = "EDITING"
    TECHNOLOGY = "TECHNOLOGY"
    OTHER = "OTHER"


class DomainType(str, Enum):
    ACADEMIC = "ACADEMIC"
    RESEARCH = "RESEARCH"
    SOFTWARE = "SOFTWARE"
    MATHEMATICS = "MATHEMATICS"
    SCIENCE = "SCIENCE"
    BUSINESS = "BUSINESS"
    FINANCE = "FINANCE"
    FOREX = "FOREX"
    LEGAL = "LEGAL"
    CREATIVE = "CREATIVE"
    GENERAL = "GENERAL"


class TaskType(str, Enum):
    QUESTION_ANSWERING = "QUESTION_ANSWERING"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    IMAGE_ANALYSIS = "IMAGE_ANALYSIS"
    OCR = "OCR"
    CODE_REASONING = "CODE_REASONING"
    CREATIVE_GENERATION = "CREATIVE_GENERATION"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    COMPARISON = "COMPARISON"
    SUMMARIZATION = "SUMMARIZATION"
    PLANNING = "PLANNING"
    GENERAL_QA = "GENERAL_QA"
    TUTORING = "TUTORING"
    SYSTEM_DIAGNOSTICS = "SYSTEM_DIAGNOSTICS"



class CapabilityType(str, Enum):
    TEXT_REASONING = "TEXT_REASONING"
    LONG_CONTEXT = "LONG_CONTEXT"
    VISION = "VISION"
    OCR = "OCR"
    DOCUMENT_ANALYSIS = "DOCUMENT_ANALYSIS"
    CODE_REASONING = "CODE_REASONING"
    MATHEMATICAL_REASONING = "MATHEMATICAL_REASONING"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    CREATIVE_GENERATION = "CREATIVE_GENERATION"
    UI_DESIGN = "UI_DESIGN"
    EMBEDDING = "EMBEDDING"
    RERANKING = "RERANKING"


class ObservationProvenance(str, Enum):
    OBSERVED = "OBSERVED"
    OCR_DETECTED = "OCR_DETECTED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    NOT_FOUND = "NOT_FOUND"


class KnowledgeSource(str, Enum):
    USER_PROVIDED = "USER_PROVIDED"
    UPLOADED_DOCUMENT = "UPLOADED_DOCUMENT"
    IMAGE_OBSERVATION = "IMAGE_OBSERVATION"
    OCR = "OCR"
    CONVERSATION = "CONVERSATION"
    MEMORY = "MEMORY"
    MODEL_KNOWLEDGE = "MODEL_KNOWLEDGE"
    INFERENCE = "INFERENCE"
    CALCULATION = "CALCULATION"
    WEB_SOURCE = "WEB_SOURCE"
    INTERNAL_KNOWLEDGE = "INTERNAL_KNOWLEDGE"


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    NORMALIZING = "NORMALIZING"
    CLASSIFYING = "CLASSIFYING"
    COLLECTING_EVIDENCE = "COLLECTING_EVIDENCE"
    ROUTING = "ROUTING"
    REASONING = "REASONING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskComplexity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class EvidenceProvenance(BaseModel):
    source_file: str
    source_type: str
    page: Optional[int] = None
    section: Optional[str] = None
    row_or_line: Optional[str] = None
    confidence: float = 1.0


class EvidenceItem(BaseModel):
    evidence_id: str
    source_file_id: str
    filename: str
    source_type: str
    content: str
    normalized_content: str
    sha256: str
    extraction_method: str = "text_parser"
    confidence: float = 1.0
    provenance: EvidenceProvenance
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OCRBoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class OCRToken(BaseModel):
    text: str
    confidence: float
    bounding_box: Optional[OCRBoundingBox] = None
    provenance: ObservationProvenance = ObservationProvenance.OCR_DETECTED


class OCRResultData(BaseModel):
    extracted_text: str
    confidence: float
    tokens: List[OCRToken] = []
    detected_language: str = "en"
    source_id: str
    extraction_method: str = "tesseract_mock_safe"
    uncertain: bool = False
    warning: Optional[str] = None


class VisualEvidence(BaseModel):
    visual_id: str
    filename: str
    provenance: ObservationProvenance
    element_type: str
    description: str
    confidence: float = 1.0
    bounding_box: Optional[OCRBoundingBox] = None


class TaskContract(BaseModel):
    contract_id: str
    request_id: str
    tenant_id: str
    user_id: str
    intent: IntentType
    domain: DomainType
    task_type: TaskType
    user_goal: str
    input_sources: List[str] = []
    allowed_capabilities: List[CapabilityType] = []
    evidence_required: bool = False
    allowed_sources: List[KnowledgeSource] = []
    forbidden_behaviors: List[str] = [
        "invent_missing_facts",
        "fabricate_document_content",
        "fabricate_image_content",
        "use_unrelated_memory",
        "change_topic",
        "claim_unverified_information",
        "expose_secrets",
        "bypass_permissions",
    ]
    output_requirements: List[str] = ["evidence_grounded", "accurate"]
    language: str = "en"
    complexity: TaskComplexity = TaskComplexity.LOW
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ClaimItem(BaseModel):
    claim_id: str
    text: str
    claim_type: str = "factual"
    status: ClaimStatus = ClaimStatus.UNSUPPORTED
    supporting_evidence_ids: List[str] = []
    confidence: float = 0.0
    source_provenance: Optional[EvidenceProvenance] = None
    reason: str = ""


class ClaimVerificationResult(BaseModel):
    verified_claims: List[ClaimItem] = []
    unsupported_claims: List[ClaimItem] = []
    contradicted_claims: List[ClaimItem] = []
    inferred_claims: List[ClaimItem] = []
    overall_support_ratio: float = 1.0
    passed: bool = True
    summary: str = ""


class QualityGateRule(str, Enum):
    INTENT_MATCH = "INTENT_MATCH"
    TOPIC_MATCH = "TOPIC_MATCH"
    EVIDENCE_SUPPORT = "EVIDENCE_SUPPORT"
    CLAIM_SUPPORT = "CLAIM_SUPPORT"
    SOURCE_FIDELITY = "SOURCE_FIDELITY"
    LANGUAGE_MATCH = "LANGUAGE_MATCH"
    COMPLETENESS = "COMPLETENESS"
    UNCERTAINTY_CORRECTNESS = "UNCERTAINTY_CORRECTNESS"
    HALLUCINATION_CHECK = "HALLUCINATION_CHECK"
    USER_QUESTION_COVERAGE = "USER_QUESTION_COVERAGE"
    MODALITY_CORRECTNESS = "MODALITY_CORRECTNESS"
    MODEL_CAPABILITY_CORRECTNESS = "MODEL_CAPABILITY_CORRECTNESS"
    CONTEXT_CONTAMINATION_CHECK = "CONTEXT_CONTAMINATION_CHECK"
    ACADEMIC_ATTRIBUTION_CHECK = "ACADEMIC_ATTRIBUTION_CHECK"
    ANSWER_DIRECTNESS = "ANSWER_DIRECTNESS"


class QualityGateCheckResult(BaseModel):
    rule: QualityGateRule
    passed: bool
    score: float = 1.0
    reason: str = ""


class QualityGateEvaluation(BaseModel):
    passed: bool
    overall_score: float
    checks: List[QualityGateCheckResult] = []
    regeneration_needed: bool = False
    critical_failures: List[str] = []


class AnswerPlan(BaseModel):
    user_goal: str
    expected_output_format: str = "DIRECT"
    available_evidence: List[str] = []
    missing_evidence: List[str] = []
    domain: DomainType
    required_capabilities: List[CapabilityType] = []
    selected_provider: str
    selected_model: str
    relevant_context: List[str] = []
    dropped_context: List[str] = []
    planned_claims: List[str] = []
    forbidden_claims: List[str] = []
    certainty_level: str = "HIGH"


class TopicDriftEvaluation(BaseModel):
    is_drifted: bool = False
    drift_score: float = 0.0
    reason: str = "Answer is strictly relevant to user request."
    detected_unrelated_topics: List[str] = []



class AcademicSectionData(BaseModel):
    section_name: str
    content: str
    citations: List[str] = []
    provenance: str = "DOCUMENT_FACT"


class AcademicStructure(BaseModel):
    problem_statement: Optional[str] = None
    research_gap: Optional[str] = None
    general_objective: Optional[str] = None
    specific_objectives: List[str] = []
    research_questions: List[str] = []
    hypotheses: List[str] = []
    methodology: Optional[Dict[str, str]] = None
    results_summary: Optional[str] = None
    limitations: List[str] = []
    sections: List[AcademicSectionData] = []


class AttachmentPayload(BaseModel):
    filename: str
    file_type: str = "txt"
    mime_type: str = "text/plain"
    content_bytes: Any = ""
    size_bytes: int = 0
    visual_elements: List[Any] = []
    ocr_confidence: float = 0.95



class IntelligenceRequest(BaseModel):
    request_id: Optional[str] = None
    message: str
    mode: Optional[str] = "Academic"
    language: Optional[str] = "en"
    conversation_id: Optional[str] = None
    workspace_id: Optional[str] = None
    files: List[Dict[str, Any]] = []
    images: List[Dict[str, Any]] = []
    attachments: List[AttachmentPayload] = []
    history: List[Dict[str, Any]] = []
    constraints: List[str] = []
    expected_output: Optional[str] = None
    requested_detail_level: Optional[str] = "DETAILED"



class DecisionTrace(BaseModel):
    step: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    details: Dict[str, Any] = {}


class IntelligenceResult(BaseModel):
    task_id: str
    request_id: str
    tenant_id: str
    status: TaskStatus
    answer: str
    intent: IntentType
    domain: DomainType
    task_type: TaskType
    evidence_items: List[EvidenceItem] = []
    visual_evidence: List[VisualEvidence] = []
    ocr_results: List[OCRResultData] = []
    claims: List[ClaimItem] = []
    claim_verification: Optional[ClaimVerificationResult] = None
    topic_drift: Optional[TopicDriftEvaluation] = None
    selected_provider: str = "internal_engine"
    selected_model: str = "pjkronx-grounded-intelligence-v4"
    capabilities_used: List[CapabilityType] = []
    confidence: float = 1.0
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    traces: List[DecisionTrace] = []
    warnings: List[str] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
