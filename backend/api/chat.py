from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import re

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    mode: str
    language: str
    conversation_id: str
    history: List[Message] = []

def fix_response(text: str) -> str:
    if not text:
        return ""
    # Normalize excessive vertical spacing (max 2 consecutive newlines)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Ensure code blocks have clean newline boundaries
    text = re.sub(r'```(\w+)\s*', r'\n```\1\n', text)
    return text.strip()

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        from orchestrator.core import KronxOrchestrator
        orchestrator = KronxOrchestrator()
        response = await orchestrator.process(
            message=request.message,
            mode=request.mode,
            language=request.language,
            conversation_id=request.conversation_id,
            history=request.history
        )
        return {"response": fix_response(response)}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        from orchestrator.core import KronxOrchestrator
        orchestrator = KronxOrchestrator()

        async def generate():
            try:
                async for chunk in orchestrator.stream(
                    message=request.message,
                    mode=request.mode,
                    language=request.language,
                    conversation_id=request.conversation_id,
                    history=request.history
                ):
                    if chunk:
                        # Escape newlines for SSE payload encoding if necessary, or stream raw chunk json
                        payload = chunk.replace("\n", "\\n")
                        yield f"data: {payload}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                err_msg = str(e).replace("\n", " ")
                yield f"data: Error: {err_msg}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        return {"error": str(e)}