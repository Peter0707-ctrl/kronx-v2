"""
Phase 4.0 — Task Contract Engine
Generates immutable task contracts defining precise goals, input sources, allowed capabilities, and strictly forbidden behaviors.
"""
from __future__ import annotations
import uuid
from typing import Dict, Any, List, Optional
from intelligence.schemas import (
    TaskContract, IntentType, DomainType, TaskType, CapabilityType,
    KnowledgeSource, TaskComplexity
)


class TaskContractGenerator:
    """Creates authoritative contracts for user requests before intelligence execution."""

    @staticmethod
    def estimate_complexity(message: str, has_files: bool, has_images: bool, file_count: int) -> TaskComplexity:
        msg_len = len(message.split())
        if file_count > 1:
            return TaskComplexity.VERY_HIGH
        if has_files or has_images or msg_len > 100:
            return TaskComplexity.HIGH
        if msg_len > 30 or any(w in message.lower() for w in ["methodology", "compare", "analyze", "explain in detail", "solve"]):
            return TaskComplexity.MEDIUM
        return TaskComplexity.LOW

    @classmethod
    def create_contract(
        cls,
        request_id: str,
        tenant_id: str,
        user_id: str,
        normalized_data: Dict[str, Any],
        intent_data: Dict[str, Any],
        uploaded_sources: Optional[List[str]] = None,
    ) -> TaskContract:
        """Constructs an immutable TaskContract."""
        intent: IntentType = intent_data["primary_intent"]
        domain: DomainType = intent_data["domain"]
        task_type: TaskType = intent_data["task_type"]
        capabilities: List[CapabilityType] = intent_data["required_capabilities"]
        evidence_required: bool = intent_data["evidence_required"]

        sources = list(uploaded_sources or [])

        # Allowed Knowledge Sources
        allowed_sources: List[KnowledgeSource] = []
        if normalized_data.get("has_files"):
            allowed_sources.append(KnowledgeSource.UPLOADED_DOCUMENT)
        if normalized_data.get("has_images"):
            allowed_sources.extend([KnowledgeSource.IMAGE_OBSERVATION, KnowledgeSource.OCR])
        allowed_sources.extend([KnowledgeSource.USER_PROVIDED, KnowledgeSource.INTERNAL_KNOWLEDGE, KnowledgeSource.MODEL_KNOWLEDGE])

        # Forbidden behaviors tailored to task
        forbidden = [
            "invent_missing_facts",
            "fabricate_document_content",
            "fabricate_image_content",
            "use_unrelated_memory",
            "change_topic",
            "claim_unverified_information",
            "expose_secrets",
            "bypass_permissions",
        ]

        if intent in [IntentType.DOCUMENT_ANALYSIS, IntentType.ACADEMIC, IntentType.MULTI_DOCUMENT_ANALYSIS]:
            forbidden.extend(["substitute_general_knowledge_for_document_facts", "hallucinate_citations"])

        if intent == IntentType.IMAGE_ANALYSIS:
            forbidden.extend(["generate_image_instead_of_analysis", "hallucinate_hidden_text"])

        if intent == IntentType.IMAGE_GENERATION:
            forbidden.extend(["analyze_image_instead_of_generating"])

        complexity = cls.estimate_complexity(
            message=normalized_data["clean_message"],
            has_files=normalized_data["has_files"],
            has_images=normalized_data["has_images"],
            file_count=normalized_data["file_count"],
        )

        return TaskContract(
            contract_id=f"cnt_{uuid.uuid4().hex[:10]}",
            request_id=request_id,
            tenant_id=tenant_id,
            user_id=user_id,
            intent=intent,
            domain=domain,
            task_type=task_type,
            user_goal=normalized_data["clean_message"],
            input_sources=sources,
            allowed_capabilities=capabilities,
            evidence_required=evidence_required,
            allowed_sources=allowed_sources,
            forbidden_behaviors=forbidden,
            output_requirements=["evidence_grounded", "accurate", normalized_data["detail_level"].lower()],
            language=normalized_data["language"],
            complexity=complexity,
        )
