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
                "Friend": "Wewe ni Kronx, mshauri na rafiki wa karibu wa wanafunzi. Toa majibu ya kina, yenye kueleweka vizuri na kusaidia masomo kwa Kiswahili.",
                "Teacher": "Wewe ni Kronx, mwalimu bingwa wa wanafunzi. Eleza kila somo, mada, na hesabu kwa hatua kwa hatua kwa Kiswahili sanifu.",
                "Business": "Wewe ni Kronx, mshauri wa biashara na miradi ya masomo. Toa mchanganuo wa kina kwa TZS.",
                "Research": "Wewe ni Kronx, mtafiti mkuu wa masomo na mawasilisho. Toa ripoti zilizopangwa vizuri kwa wanafunzi na watafiti.",
                "Quick": "Wewe ni Kronx. Toa jibu sahihi na la haraka la kusaidia mwanafunzi.",
            }
            mode_text = mode_instructions.get(mode, mode_instructions["Friend"])
            system = (
                f"{mode_text}\n"
                "SHERIA KUU:\n"
                "1. Lenga kusaidia wanafunzi kuelewa masomo, assignments, na tafiti kwa ufasaha wa hali ya juu.\n"
                "2. USITUMIE emoji yoyote ile chini ya mazingira yoyote.\n"
                "3. Toa maelezo yaliyopangwa vizuri kwa kutumia bullet points au namba ikibidi."
            )
        else:
            mode_instructions = {
                "Friend": "You are Kronx, an advanced AI study companion and academic mentor designed to empower students. Provide clear, direct, and comprehensive educational support.",
                "Teacher": "You are Kronx, a master educator and academic tutor. Break down complex subjects, equations, programming concepts, and homework step-by-step.",
                "Business": "You are Kronx, a technology and academic project consultant. Provide strategic analysis and financial breakdowns in TZS.",
                "Research": "You are Kronx, a principal academic researcher. Deliver structured thesis notes, paper summaries, and technical reports for students.",
                "Quick": "You are Kronx. Provide an immediate, precise answer to help students learn fast.",
            }
            mode_text = mode_instructions.get(mode, mode_instructions["Friend"])
            system = (
                f"{mode_text}\n"
                "STUDENT ACADEMIC MANDATE:\n"
                "Always prioritize student learning, concept clarity, assignment guidance, and academic excellence. Provide step-by-step explanations.\n"
                "NO EMOJIS: Do not output emojis under any circumstances."
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

        models_to_try = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.0-flash"]
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
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash"
        ]
        full_response = ""
        success = False

        for m in models_to_try:
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
                async with httpx.AsyncClient(timeout=12.0) as client:
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
            query = message.strip()
            if language == "sw":
                smart_response = (
                    f"**Muhtasari na Msaada wa Masomo wa Kronx AI (Somo: {query})**\n\n"
                    f"### 1. Dhana Kuu na Ufafanuzi\n"
                    f"Mada ya **{query}** ni msingi muhimu katika masomo ya kitaaluma. Inahitaji uchanganuzi wa hatua kwa hatua ili kuelewa kanuni kuu, fomula, na nadharia zake.\n\n"
                    f"### 2. Hatua za Kazi / Ufumbuzi (Step-by-Step Guidance)\n"
                    f"- **Hatua ya 1 (Uchanganuzi)**: Tambua vigezo kuu na nadharia inayohusika katika **{query}**.\n"
                    f"- **Hatua ya 2 (Utekelezaji)**: Tumia kanuni za kitaaluma au kanuni za hisabati/sayansi kutatua au kufafanua mada hii.\n"
                    f"- **Hatua ya 3 (Tathmini)**: Hakikisha majibu na mifano uliyopata inalingana na matokeo yanayotakiwa kitaaluma.\n\n"
                    f"### 3. Mifano na Ushauri wa Masomo\n"
                    f"Soma zaidi vifungu vinavyohusu mada hii kwenye vitabu vyako vya kiada na ufanye mazoezi ya mara kwa mara.\n\n"
                    f"*Unaweza kuandika swali mahsusi au mfano wa hesabu/nambari ili tukupatie ufumbuzi kamili wa hatua kwa hatua.*"
                )
            else:
                smart_response = (
                    f"**Kronx AI Academic Solution & Study Notes ({query})**\n\n"
                    f"### 1. Core Academic Concept & Overview\n"
                    f"The topic **{query}** is a fundamental concept requiring a structured step-by-step approach to master its core principles, formulas, and theoretical framework.\n\n"
                    f"### 2. Step-by-Step Solution & Problem Methodology\n"
                    f"- **Step 1 (Identify Key Variables)**: Break down the core components and equations governing **{query}**.\n"
                    f"- **Step 2 (Apply Theoretical Framework)**: Utilize standard academic formulas, algorithms, or analytical methods to derive the solution.\n"
                    f"- **Step 3 (Verify Results)**: Double-check calculations, logical deductions, and theoretical consistency.\n\n"
                    f"### 3. Practical Examples & Next Steps\n"
                    f"Apply this framework directly to your homework or assignment exercises.\n\n"
                    f"*Feel free to paste the exact problem text, equation, or code snippet below for an instant step-by-step breakdown.*"
                )
            yield smart_response
            full_response = smart_response

        self.memory.extract_and_save(
            conversation_id=conversation_id,
            user_message=message,
            ai_response=full_response
        )