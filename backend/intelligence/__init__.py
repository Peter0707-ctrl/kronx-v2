"""
Phase 4.1 — Copetra Intelligence Package
Universal Intelligence, Grounded Reasoning, Multimodal Accuracy & Academic Intelligence Engine.
"""
from intelligence.schemas import (
    IntentType, DomainType, TaskType, CapabilityType, ObservationProvenance,
    KnowledgeSource, ClaimStatus, TaskStatus, TaskComplexity, TaskContract,
    EvidenceItem, EvidenceProvenance, VisualEvidence, OCRResultData, OCRToken,
    OCRBoundingBox, ClaimItem, ClaimVerificationResult, TopicDriftEvaluation,
    AcademicStructure, IntelligenceRequest, IntelligenceResult, DecisionTrace
)
from intelligence.errors import (
    IntelligenceError, INTENT_UNRESOLVED, CONTRACT_VIOLATION, EVIDENCE_NOT_FOUND,
    EVIDENCE_EXTRACTION_FAILED, CLAIM_UNSUPPORTED, TOPIC_DRIFT_DETECTED,
    UNAUTHORIZED_CAPABILITY, PROVIDER_UNAVAILABLE, ROUTING_FAILED,
    TASK_NOT_FOUND, TASK_CANCELLED, TASK_ALREADY_COMPLETED, PROMPT_INJECTION_DETECTED
)
from intelligence.parsers import SpecializedParsers
from intelligence.quality_gate import QualityGate, QualityGateResult, CheckResult
from intelligence.normalizer import RequestNormalizer
from intelligence.intent import IntentClassifier
from intelligence.contract import TaskContractGenerator
from intelligence.relevance import ContextRelevanceFilter
from intelligence.evidence import EvidenceEngine
from intelligence.document_grounding import DocumentGroundingEngine
from intelligence.image_grounding import ImageGroundingEngine
from intelligence.academic import AcademicIntelligenceEngine
from intelligence.multi_document import MultiDocumentEngine
from intelligence.claim_verifier import ClaimVerifier
from intelligence.topic_guard import TopicGuard
from intelligence.routing import CapabilityRouter
from intelligence.store import IntelligenceStore
from intelligence.audit import log_intelligence_audit
from intelligence.orchestrator import CopetraIntelligenceOrchestrator

__all__ = [
    "IntentType",
    "DomainType",
    "TaskType",
    "CapabilityType",
    "ObservationProvenance",
    "KnowledgeSource",
    "ClaimStatus",
    "TaskStatus",
    "TaskComplexity",
    "TaskContract",
    "EvidenceItem",
    "EvidenceProvenance",
    "VisualEvidence",
    "OCRResultData",
    "OCRToken",
    "OCRBoundingBox",
    "ClaimItem",
    "ClaimVerificationResult",
    "TopicDriftEvaluation",
    "AcademicStructure",
    "IntelligenceRequest",
    "IntelligenceResult",
    "DecisionTrace",
    "IntelligenceError",
    "INTENT_UNRESOLVED",
    "CONTRACT_VIOLATION",
    "EVIDENCE_NOT_FOUND",
    "EVIDENCE_EXTRACTION_FAILED",
    "CLAIM_UNSUPPORTED",
    "TOPIC_DRIFT_DETECTED",
    "UNAUTHORIZED_CAPABILITY",
    "PROVIDER_UNAVAILABLE",
    "ROUTING_FAILED",
    "TASK_NOT_FOUND",
    "TASK_CANCELLED",
    "TASK_ALREADY_COMPLETED",
    "PROMPT_INJECTION_DETECTED",
    "SpecializedParsers",
    "QualityGate",
    "QualityGateResult",
    "CheckResult",
    "RequestNormalizer",
    "IntentClassifier",
    "TaskContractGenerator",
    "ContextRelevanceFilter",
    "EvidenceEngine",
    "DocumentGroundingEngine",
    "ImageGroundingEngine",
    "AcademicIntelligenceEngine",
    "MultiDocumentEngine",
    "ClaimVerifier",
    "TopicGuard",
    "CapabilityRouter",
    "IntelligenceStore",
    "log_intelligence_audit",
    "CopetraIntelligenceOrchestrator",
]
