"""
Phase 4.0 — Capability & Model Routing Engine
Dynamically selects models and provider endpoints based on required capabilities, complexity, and health without hard-coded assumptions.
"""
from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
from intelligence.schemas import TaskContract, CapabilityType, TaskComplexity


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
        Determines the optimal provider and model based on capabilities and complexity.
        """
        providers = cls.get_available_providers()
        caps = contract.allowed_capabilities
        complexity = contract.complexity

        # 1. Vision Tasks
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
        if CapabilityType.CREATIVE_GENERATION in caps:
            return {
                "provider": "pollinations_safe",
                "model": "pollinations-image-synth",
                "capabilities": [CapabilityType.CREATIVE_GENERATION],
                "fallback_provider": "internal_grounded",
            }

        # 3. High Complexity / Long Context Academic Tasks
        if complexity in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH] or CapabilityType.LONG_CONTEXT in caps:
            if providers["groq"]:
                return {
                    "provider": "groq",
                    "model": "llama-3.3-70b-versatile",
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

        # 4. Standard Fast / Medium Tasks
        if providers["groq"]:
            return {
                "provider": "groq",
                "model": "llama-3.1-8b-instant",
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

        # 5. High-Precision Internal Grounded Fallback
        return {
            "provider": "internal_grounded",
            "model": "pjkronx-grounded-intelligence-v4",
            "capabilities": [CapabilityType.TEXT_REASONING, CapabilityType.DOCUMENT_ANALYSIS],
            "fallback_provider": None,
        }
