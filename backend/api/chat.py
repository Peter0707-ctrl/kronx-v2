from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import re
import asyncio
from utils.logger import logger

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
    """Standard (non-streaming) chat endpoint with full failover."""
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
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return {"response": "Error processing your request. Please try again."}

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE Streaming chat endpoint.
    CRITICAL FIX: Sends an initial keep-alive byte immediately to prevent
    Railway/nginx proxy from buffering the response and timing out.
    """
    try:
        from orchestrator.core import KronxOrchestrator
        orchestrator = KronxOrchestrator()

        async def generate():
            try:
                # ── CRITICAL: Send initial flush ping immediately ──
                # This prevents Railway/nginx from buffering the stream
                # and forces the connection open before heavy processing starts
                yield ": pjkronx-stream-open\n\n"
                await asyncio.sleep(0)  # Yield control to event loop

                full_text = ""
                async for chunk in orchestrator.stream(
                    message=request.message,
                    mode=request.mode,
                    language=request.language,
                    conversation_id=request.conversation_id,
                    history=request.history
                ):
                    if chunk:
                        full_text += chunk
                        # Clean SSE payload: escape newlines for SSE wire format
                        clean_chunk = chunk.replace("\r", "").replace("\n", "\\n")
                        yield f"data: {clean_chunk}\n\n"
                        await asyncio.sleep(0)  # Yield to event loop after each chunk

                yield "data: [DONE]\n\n"

            except Exception as e:
                # On error, yield a proper error response instead of crashing
                err_text = f"Error: {str(e).replace(chr(10), ' ')}"
                yield f"data: {err_text}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",        # Disable nginx buffering
                "Transfer-Encoding": "chunked",    # Force chunked transfer
                "Content-Type": "text/event-stream; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error in chat_stream setup: {e}", exc_info=True)
        # Fallback to JSON if streaming setup fails entirely
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
            return JSONResponse({"response": fix_response(response)})
        except Exception as e2:
            logger.error(f"Error in fallback JSON response: {e2}", exc_info=True)
            return JSONResponse({"response": "An internal error occurred. Please try again later."})