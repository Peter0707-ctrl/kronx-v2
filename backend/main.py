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

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def root():
    return """<!DOCTYPE html>
<html>
<head>
    <meta name="google-site-verification" content="4jBwESfIU4dUQ8-AJiw6Otam1M-JDsIGmQJ2WJnZZ8U" />
    <title>Kronx API</title>
</head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
    <h1>Kronx AI Backend API</h1>
    <p>Status: Running &amp; Operational</p>
</body>
</html>"""

@app.get("/googlef5f0aa224a2f0db3.html", response_class=HTMLResponse)
def google_file():
    return "google-site-verification: googlef5f0aa224a2f0db3.html"

from fastapi.responses import Response

@app.get("/sitemap.xml")
def sitemap_xml():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://profound-rejoicing-production-1ce5.up.railway.app/</loc>
    <lastmod>2026-08-01</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://profound-rejoicing-production-1ce5.up.railway.app/chat</loc>
    <lastmod>2026-08-01</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://profound-rejoicing-production-1ce5.up.railway.app/landing</loc>
    <lastmod>2026-08-01</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://profound-rejoicing-production-1ce5.up.railway.app/admin</loc>
    <lastmod>2026-08-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    return Response(content=content, media_type="application/xml")

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
