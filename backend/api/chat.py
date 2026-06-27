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
    # Fix code blocks — add newlines after opening ```
    text = re.sub(r'```(\w+)', r'\n```\1\n', text)
    # Fix closing code blocks
    text = re.sub(r'```\s*', r'\n```\n', text)
    # Fix headers
    text = re.sub(r'##\s+', r'\n## ', text)
    text = re.sub(r'###\s+', r'\n### ', text)
    # Fix bullet points
    text = re.sub(r'•\s+', r'\n• ', text)
    text = re.sub(r'\*\s+(?!\*)', r'\n* ', text)
    # Fix numbered lists
    text = re.sub(r'(\d+\.)\s+', r'\n\1 ', text)
    # Fix sentences running together
    text = re.sub(r'\.\s+([A-Z])', r'.\n\1', text)
    # Remove triple+ newlines
    text = re.sub(r'\n{3,}', r'\n\n', text)
    # Fix code content — semicolons followed by keywords
    text = re.sub(r';\s*(int|char|void|printf|return|for|if|while|#)', r';\n    \1', text)
    text = re.sub(r'\{\s*(int|char|void|printf|return|for|if|while|#)', r'{\n    \1', text)
    text = re.sub(r'\}\s*(int|char|void|printf|return|for|if|while|#)', r'}\n\1', text)
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
            full = ""
            try:
                async for chunk in orchestrator.stream(
                    message=request.message,
                    mode=request.mode,
                    language=request.language,
                    conversation_id=request.conversation_id,
                    history=request.history
                ):
                    full += chunk
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "http://localhost:3000",
            }
        )
    except Exception as e:
        return {"error": str(e)}