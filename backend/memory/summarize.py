import os
from typing import List
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:0.5b")

class ConversationSummarizer:
    def __init__(self, model: str = None):
        self.model = model or DEFAULT_MODEL
        self.base_url = OLLAMA_URL

    async def summarize_async(self, messages: List[dict]) -> str:
        """
        Summarize a list of messages asynchronously into key points.
        """
        if not messages:
            return ""

        conversation_text = ""
        for msg in messages[-8:]:
            role = "User" if msg.get("role") == "user" else "Kronx"
            content = msg.get("content", "")[:150]
            conversation_text += f"{role}: {content}\n"

        prompt = f"""Summarize this conversation in 3 short bullet points.
Focus on: user goals, key facts, decisions made. Be very brief.

Conversation:
{conversation_text}

Summary:"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 100,
                            "temperature": 0.3
                        }
                    }
                )
                data = response.json()
                return data.get("response", "").strip()
        except Exception as e:
            print(f"Summarizer error: {e}")
            return ""

    def summarize(self, messages: List[dict]) -> str:
        """Fallback synchronous extraction."""
        facts = []
        for msg in messages[-6:]:
            if msg.get("role") == "user":
                facts.extend(self.extract_key_facts(msg.get("content", "")))
        return "\n".join(facts) if facts else ""

    def extract_key_facts(self, text: str) -> List[str]:
        """
        Extract key facts from a piece of text using rules.
        """
        facts = []
        fact_indicators = [
            "I am", "I'm", "My name", "I live", "I work",
            "I want", "I need", "I have", "My goal",
            "Mimi ni", "Jina langu", "Ninaishi", "Ninafanya kazi",
            "Nataka", "Ninahitaji", "Nina", "Lengo langu"
        ]

        sentences = text.split(".")
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator.lower() in sentence.lower() 
                   for indicator in fact_indicators):
                if len(sentence) > 8:
                    facts.append(sentence)

        return facts[:3]