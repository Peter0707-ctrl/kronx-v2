import requests
import json
from typing import List, AsyncGenerator
from dotenv import load_dotenv
from memory.manager import MemoryManager

load_dotenv()

OLLAMA_URL = "http://localhost:11434"
MODEL = "tinyllama"


class KronxOrchestrator:
    def __init__(self):
        self.model = MODEL
        self.base_url = OLLAMA_URL
        self.memory = MemoryManager()

    def _build_system_prompt(self, mode: str, language: str, memory_context: str = "") -> str:
        mode_instructions = {
            "Friend": "You are a warm friendly companion.",
            "Teacher": "You are a patient teacher. Explain step by step.",
            "Business": "You are a business advisor. Give practical advice.",
            "Research": "You are a researcher. Give detailed information.",
            "Quick": "Give very short direct answers only.",
        }

        lang = "Respond in Swahili." if language == "sw" else "Respond in English."
        mode_text = mode_instructions.get(mode, mode_instructions["Friend"])

        system = f"""{mode_text}
{lang}

You are Kronx — AI companion for Tanzania, East Africa.
- Use TZS for money
- Reference Dar es Salaam, Arusha, Mwanza when relevant
- Give practical real advice for Tanzania
- NEVER write code unless user specifically asks for code
- Use bullet points and headers to organize answers
- Be concise and clear
"""
        if memory_context:
            system += f"\n{memory_context}"
        return system

    def _build_messages(self, history: List, message: str) -> List:
        messages = []
        for h in history[-6:]:
            role = h.role if h.role != "ai" else "assistant"
            if role in ["user", "assistant"]:
                messages.append({"role": role, "content": h.content})
        messages.append({"role": "user", "content": message})
        return messages

    async def process(
        self,
        message: str,
        mode: str,
        language: str,
        conversation_id: str,
        history: List
    ) -> str:
        memory_context = self.memory.get_context(conversation_id)
        system = self._build_system_prompt(mode, language, memory_context)
        messages = self._build_messages(history, message)

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": False,
            "options": {
                "num_predict": 512,
                "temperature": 0.7
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            data = response.json()
            result = data["message"]["content"]
        except Exception as e:
            result = f"Hitilafu — tafadhali jaribu tena. ({str(e)})"

        self.memory.extract_and_save(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=result
        )
        return result

    async def stream(
        self,
        message: str,
        mode: str,
        language: str,
        conversation_id: str,
        history: List
    ) -> AsyncGenerator[str, None]:
        memory_context = self.memory.get_context(conversation_id)
        system = self._build_system_prompt(mode, language, memory_context)
        messages = self._build_messages(history, message)

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}] + messages,
            "stream": True,
            "options": {
                "num_predict": 512,
                "temperature": 0.7
            }
        }

        full_response = ""

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=60
            )

            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_response += chunk
                            yield chunk
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            yield f"Hitilafu — {str(e)}"

        self.memory.extract_and_save(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=full_response
        )