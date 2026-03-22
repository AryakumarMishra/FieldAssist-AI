from pydantic import BaseModel
from typing import List, Optional

class ChatSessionCreate(BaseModel):
    title: str
    category: str

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    category: str
    created_at: str

class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    timestamp: str
