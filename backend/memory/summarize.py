from typing import List
import requests
import json

OLLAMA_URL = "http://localhost:11434"
MODEL = "qwen2:0.5b"

class ConversationSummarizer:
    def __init__(self):
        self.model = MODEL
        self.base_url = OLLAMA_URL

    def summarize(self, messages: List[dict]) -> str:
        """
        Summarize a list of messages into key points.
        """
        if not messages:
            return ""

        # Build conversation text
        conversation_text = ""
        for msg in messages[-10:]:  # Last 10 messages
            role = "User" if msg.get("role") == "user" else "Kronx"
            content = msg.get("content", "")[:200]  # Limit length
            conversation_text += f"{role}: {content}\n"

        prompt = f"""Summarize this conversation in 3 short bullet points.
Focus on: what the user wants, key facts mentioned, decisions made.
Be very brief.

Conversation:
{conversation_text}

Summary:"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 150,
                        "temperature": 0.3
                    }
                },
                timeout=30
            )
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            print(f"Summarizer error: {e}")
            return ""

    def extract_key_facts(self, text: str) -> List[str]:
        """
        Extract key facts from a piece of text.
        """
        facts = []

        # Simple rule-based extraction
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
                if len(sentence) > 10:
                    facts.append(sentence)

        return facts[:3]  # Return max 3 facts