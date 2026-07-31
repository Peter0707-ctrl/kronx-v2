from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Kronx API",
    description="Kronx AI Companion Backend",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.chat import router as chat_router
from api.memory import router as memory_router
app.include_router(chat_router, prefix="/api")
app.include_router(memory_router, prefix="/api")

@app.get("/")
def root():
    return {
        "name": "Kronx API",
        "version": "0.3.0",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/system/status")
async def system_status():
    from orchestrator.core import KronxOrchestrator
    from memory.store import MemoryStore
    orchestrator = KronxOrchestrator()
    store = MemoryStore()
    active_model = await orchestrator.get_active_model()
    memories_data = store._load()
    total_memories = sum(len(v) for v in memories_data.values()) if memories_data else 0
    return {
        "status": "online",
        "active_model": active_model,
        "ollama_url": orchestrator.base_url,
        "ram_optimization": "low_ram_mode_active",
        "total_memories": total_memories,
        "active_conversations_in_store": len(memories_data) if memories_data else 0
    }
