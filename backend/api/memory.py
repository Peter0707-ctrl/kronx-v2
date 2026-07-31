from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from memory.store import MemoryStore

router = APIRouter()
store = MemoryStore()

class MemoryDeleteRequest(BaseModel):
    conversation_id: str
    memory_id: str

@router.get("/memories/{conversation_id}")
async def get_memories(conversation_id: str):
    try:
        memories = store.get_memories(conversation_id, limit=20)
        user_facts = store.get_user_facts("default_user")
        return {
            "conversation_memories": memories,
            "user_facts": user_facts,
            "total_count": len(memories) + len(user_facts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memories/{conversation_id}/{memory_id}")
async def delete_memory(conversation_id: str, memory_id: str):
    try:
        store.delete_memory(conversation_id, memory_id)
        return {"status": "deleted", "memory_id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
