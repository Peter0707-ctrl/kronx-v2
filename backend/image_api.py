import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kronx Image API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageReq(BaseModel):
    prompt: str

@app.post("/api/generate-image")
async def generate_image(req: ImageReq):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    encoded = httpx.URL(prompt).raw_path.decode('utf-8') if prompt else "artwork"
    # Use Pollinations AI & Unsplash dynamic keyword search
    pollinations_url = f"https://pollinations.ai/p/{httpx.URL(prompt).path}?width=1280&height=720&seed=42&nologo=true"
    unsplash_url = f"https://source.unsplash.com/1200x700/?{encoded}"
    
    return {
        "status": "success",
        "prompt": prompt,
        "image_url": pollinations_url,
        "backup_url": unsplash_url
    }
