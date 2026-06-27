from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageSchema(BaseModel):
    role: str
    content: str

class ChatRequestSchema(BaseModel):
    message: str
    mode: str = "Friend"
    language: str = "sw"
    conversation_id: str
    history: List[MessageSchema] = []

class ChatResponseSchema(BaseModel):
    response: str
    conversation_id: str
    mode: str
    language: str

class ConversationSchema(BaseModel):
    id: str
    title: str
    mode: str
    language: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageSchema] = []

class MemorySchema(BaseModel):
    id: str
    user_id: str
    content: str
    importance: float = 1.0
    created_at: datetime

class UserSchema(BaseModel):
    id: str
    name: str
    email: str
    language: str = "sw"
    region: str = "Dar es Salaam"
    created_at: datetime

class HealthSchema(BaseModel):
    status: str
    version: str
    model: str