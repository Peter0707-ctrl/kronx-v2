from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from memory.store import MemoryStore
import asyncio

from utils.logger import logger

router = APIRouter()
store = MemoryStore()

class MemoryDeleteRequest(BaseModel):
    conversation_id: str
    memory_id: str

@router.get("/memories/{conversation_id}")
async def get_memories(conversation_id: str):
    try:
        memories = await asyncio.to_thread(store.get_memories, conversation_id, limit=20)
        user_facts = await asyncio.to_thread(store.get_user_facts, "default_user")
        return {
            "conversation_memories": memories,
            "user_facts": user_facts,
            "total_count": len(memories) + len(user_facts)
        }
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving memories.")

@router.delete("/memories/{conversation_id}/{memory_id}")
async def delete_memory(conversation_id: str, memory_id: str):
    try:
        await asyncio.to_thread(store.delete_memory, conversation_id, memory_id)
        return {"status": "deleted", "memory_id": memory_id}
    except Exception as e:
        logger.error(f"Error deleting memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error deleting memory.")
