from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Kronx API",
    description="Kronx AI Companion Backend",
    version="0.1.0"
)

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from api.chat import router as chat_router
app.include_router(chat_router, prefix="/api")

@app.get("/")
def root():
    return {
        "name": "Kronx API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}