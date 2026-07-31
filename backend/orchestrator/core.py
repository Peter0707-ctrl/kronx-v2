import os
import json
import httpx
from typing import List, AsyncGenerator
from dotenv import load_dotenv
from memory.manager import MemoryManager
from utils.helpers import get_mode_context

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


class KronxOrchestrator:
    def __init__(self):
        self.memory = MemoryManager()
        self.api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)

    def _build_system_prompt(self, mode: str, language: str, memory_context: str = "") -> str:
        """
        Build system prompt for Kronx AI powered by Gemini.
        Supports both Swahili and English depending on language parameter.
        """
        if language == "sw":
            mode_instructions = {
                "Friend": "Wewe ni Kronx, mshauri na rafiki wa karibu, mwenye akili bandia yenye kina. Toa majibu ya kina, yenye kueleweka vizuri na kwa ufasaha wa hali ya juu kwa Kiswahili.",
                "Teacher": "Wewe ni Kronx, mwalimu bingwa. Eleza kila kitu kwa hatua kwa hatua kwa Kiswahili sanifu chenye ufasaha zaidi.",
                "Business": "Wewe ni Kronx, mshauri mkuu wa biashara na fedha nchini Tanzania. Toa mchanganuo wa kina wa biashara na bajeti kwa TZS.",
                "Research": "Wewe ni Kronx, mtafiti mkuu. Toa ripoti za kina zilizopangwa vizuri kwa vichwa vya habari na vipengele kwa Kiswahili.",
                "Quick": "Wewe ni Kronx. Toa jibu sahihi na la moja kwa moja kwa Kiswahili.",
            }
            mode_text = mode_instructions.get(mode, mode_instructions["Friend"])
            system = (
                f"{mode_text}\n"
                "SHERIA KUU:\n"
                "1. Jibu kwa Kiswahili sanifu, chenye ufasaha na cha kuvutia.\n"
                "2. USITUMIE emoji yoyote ile chini ya mazingira yoyote.\n"
                "3. Toa maelezo yaliyopangwa vizuri kwa kutumia bullet points au namba ikibidi."
            )
        else:
            mode_instructions = {
                "Friend": "You are Kronx, an advanced AI pair programmer and direct solution assistant built by Google Deepmind team principles. You answer directly, concisely, and with expert technical depth. Avoid chatbot clichés.",
                "Teacher": "You are Kronx, a master computer scientist and educator. Break down topics with clear architectural steps, code examples, and concise explanations.",
                "Business": "You are Kronx, a senior technology and business consultant. Provide strategic analysis, clear plans, and financial breakdowns in TZS.",
                "Research": "You are Kronx, a principal research engineer. Deliver comprehensive reports with structured headings, code snippets, and deep technical details.",
                "Quick": "You are Kronx. Provide an immediate, precise answer.",
            }
            mode_text = mode_instructions.get(mode, mode_instructions["Friend"])
            system = (
                f"{mode_text}\n"
                "IMAGE GENERATION DIRECTIVE:\n"
                "When the user asks to create an image, draw a picture, or generate artwork, DO NOT say you cannot generate binary images and DO NOT output SVG/XML code. Instead, generate a hyper-detailed descriptive Markdown image element using Pollinations image API: `![Generated Image](https://pollinations.ai/p/{URL_ENCODED_PROMPT}?width=1280&height=720&seed=42&nologo=true)`."
            )

        system += (
            "\n\nTOPIC ADAPTABILITY MANDATE:\n"
            "Always answer the current user question directly and accurately, even if the topic has suddenly changed from previous chat history. "
            "Never confuse past discussion context with the new query."
        )

        if memory_context:
            system += f"\nContext from memory:\n{memory_context}\n"

        return system.strip()

    def _build_contents(self, history: List, message: str) -> List[dict]:
        contents = []
        for h in history[-10:]:
            role = getattr(h, "role", None) or (h.get("role") if isinstance(h, dict) else "user")
            content = getattr(h, "content", None) or (h.get("content") if isinstance(h, dict) else "")
            if role in ["user", "ai", "assistant"] and content:
                norm_role = "model" if role in ["ai", "assistant"] else "user"
                contents.append({
                    "role": norm_role,
                    "parts": [{"text": content}]
                })

        contents.append({
            "role": "user",
            "parts": [{
                "text": (
                    f"[CURRENT USER REQUEST - ANSWER THIS DIRECTLY REGARDLESS OF PREVIOUS TOPICS]:\n"
                    f"{message}"
                )
            }]
        })
        return contents

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
        contents = self._build_contents(history, message)

        models_to_try = ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
        last_err = None

        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                        self.memory.extract_and_save(
                            conversation_id=conversation_id,
                            user_message=message,
                            ai_response=result
                        )
                        return result
                    else:
                        last_err = f"HTTP {response.status_code}: {response.text}"
            except Exception as e:
                last_err = str(e)

        return f"Error generating response: {last_err}"

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
        contents = self._build_contents(history, message)

        models_to_try = [
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemma-4-31b-it",
            "gemma-4-26b-a4b-it",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite"
        ]
        full_response = ""
        success = False

        for m in models_to_try:
            # 1. Try direct generateContent API endpoint first
            direct_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(direct_url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            text_result = "".join([p.get("text", "") for p in parts]).strip()
                            if text_result:
                                full_response = text_result
                                success = True
                                yield text_result
                                break
            except Exception:
                pass

            # 2. Try streaming SSE endpoint if direct POST fails
            stream_url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:streamGenerateContent?alt=sse&key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    async with client.stream("POST", stream_url, json=payload) as response:
                        if response.status_code != 200:
                            continue
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                raw_data = line[6:].strip()
                                if not raw_data:
                                    continue
                                try:
                                    data = json.loads(raw_data)
                                    candidates = data.get("candidates", [])
                                    if candidates and "content" in candidates[0]:
                                        parts = candidates[0]["content"].get("parts", [])
                                        for part in parts:
                                            chunk = part.get("text", "")
                                            if chunk:
                                                full_response += chunk
                                                success = True
                                                yield chunk
                                except json.JSONDecodeError:
                                    continue
                        if success:
                            break
            except Exception:
                continue

        if not success:
            err_msg = "Hitilafu ndogo ya mtandao imetokea. Tafadhali jaribu tena." if language == "sw" else "A temporary network issue occurred. Please try again."
            yield err_msg
            full_response = err_msg

        self.memory.extract_and_save(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=full_response
        )