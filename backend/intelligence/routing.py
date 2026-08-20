"""
Phase 4.2 — Capability-Based Model Routing Engine
Dynamically maps required capabilities and domains to optimal providers/models without capability mismatches.
"""
from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
from intelligence.schemas import TaskContract, CapabilityType, TaskComplexity, DomainType, IntentType


class CapabilityRouter:
    """Routes intelligence tasks to optimal providers and models based on capabilities and task contracts."""

    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Discovers configured provider keys from environment."""
        return {
            "gemini": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "YOUR_GEMINI_API_KEY_HERE"),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "internal_grounded": True,
        }

    @classmethod
    def select_route(cls, contract: TaskContract) -> Dict[str, Any]:
        """
        Determines the optimal provider and model based on capabilities, domain, and complexity.
        Ensures vision tasks are NEVER routed to text-only models, and document tasks ALWAYS receive extracted evidence.
        """
        providers = cls.get_available_providers()
        caps = contract.allowed_capabilities
        complexity = contract.complexity
        domain = contract.domain
        intent = contract.intent

        # 1. Vision & Optical OCR Tasks
        if CapabilityType.VISION in caps or CapabilityType.OCR in caps:
            if providers["gemini"]:
                return {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "capabilities": [CapabilityType.VISION, CapabilityType.OCR],
                    "fallback_provider": "internal_grounded",
                }
            if providers["openai"]:
                return {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "capabilities": [CapabilityType.VISION, CapabilityType.OCR],
                    "fallback_provider": "internal_grounded",
                }
            return {
                "provider": "internal_grounded",
                "model": "pjkronx-visual-grounding-v4",
                "capabilities": [CapabilityType.OCR, CapabilityType.VISION],
                "fallback_provider": None,
            }

        # 2. Creative Image Generation
        if CapabilityType.CREATIVE_GENERATION in caps or intent == IntentType.IMAGE_GENERATION:
            return {
                "provider": "pollinations_safe",
                "model": "pollinations-image-synth",
                "capabilities": [CapabilityType.CREATIVE_GENERATION],
                "fallback_provider": "internal_grounded",
            }

        # 3. Document Analysis Tasks
        if CapabilityType.DOCUMENT_ANALYSIS in caps or contract.evidence_required:
            if providers["gemini"]:
                return {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.LONG_CONTEXT],
                    "fallback_provider": "internal_grounded",
                }
            if providers["groq"]:
                return {
                    "provider": "groq",
                    "model": "openai/gpt-oss-120b",
                    "capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.LONG_CONTEXT],
                    "fallback_provider": "internal_grounded",
                }
            return {
                "provider": "internal_grounded",
                "model": "pjkronx-document-grounding-v4",
                "capabilities": [CapabilityType.DOCUMENT_ANALYSIS, CapabilityType.TEXT_REASONING],
                "fallback_provider": None,
            }

        # 4. Academic & Research Tasks
        if domain in [DomainType.ACADEMIC, DomainType.RESEARCH] or intent == IntentType.ACADEMIC:
            if providers["groq"]:
                return {
                    "provider": "groq",
                    "model": "openai/gpt-oss-120b",
                    "capabilities": [CapabilityType.TEXT_REASONING, CapabilityType.LONG_CONTEXT],
                    "fallback_provider": "gemini" if providers["gemini"] else "internal_grounded",
                }
            if providers["gemini"]:
                return {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "capabilities": [CapabilityType.TEXT_REASONING, CapabilityType.LONG_CONTEXT],
                    "fallback_provider": "internal_grounded",
                }
            return {
                "provider": "internal_grounded",
                "model": "pjkronx-academic-engine-v4",
                "capabilities": [CapabilityType.TEXT_REASONING],
                "fallback_provider": None,
            }

        # 5. Code Reasoning & Debugging Tasks
        if domain == DomainType.SOFTWARE or CapabilityType.CODE_REASONING in caps:
            if providers["groq"]:
                return {
                    "provider": "groq",
                    "model": "openai/gpt-oss-120b",
                    "capabilities": [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
                    "fallback_provider": "gemini" if providers["gemini"] else "internal_grounded",
                }
            if providers["gemini"]:
                return {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "capabilities": [CapabilityType.CODE_REASONING, CapabilityType.TEXT_REASONING],
                    "fallback_provider": "internal_grounded",
                }
            return {
                "provider": "internal_grounded",
                "model": "pjkronx-code-engine-v4",
                "capabilities": [CapabilityType.CODE_REASONING],
                "fallback_provider": None,
            }

        # 6. Mathematics Tasks
        if domain == DomainType.MATHEMATICS or CapabilityType.MATHEMATICAL_REASONING in caps:
            if providers["gemini"]:
                return {
                    "provider": "gemini",
                    "model": "gemini-2.0-flash",
                    "capabilities": [CapabilityType.MATHEMATICAL_REASONING, CapabilityType.TEXT_REASONING],
                    "fallback_provider": "internal_grounded",
                }
            if providers["groq"]:
                return {
                    "provider": "groq",
                    "model": "openai/gpt-oss-120b",
                    "capabilities": [CapabilityType.MATHEMATICAL_REASONING, CapabilityType.TEXT_REASONING],
                    "fallback_provider": "internal_grounded",
                }

        # 7. General Fast Tasks
        if providers["groq"]:
            return {
                "provider": "groq",
                "model": "openai/gpt-oss-20b",
                "capabilities": [CapabilityType.TEXT_REASONING],
                "fallback_provider": "internal_grounded",
            }
        if providers["gemini"]:
            return {
                "provider": "gemini",
                "model": "gemini-2.0-flash-lite",
                "capabilities": [CapabilityType.TEXT_REASONING],
                "fallback_provider": "internal_grounded",
            }

        # 8. High-Precision Internal Grounded Engine Fallback
        return {
            "provider": "internal_grounded",
            "model": "pjkronx-grounded-intelligence-v4",
            "capabilities": [CapabilityType.TEXT_REASONING],
            "fallback_provider": None,
        }
