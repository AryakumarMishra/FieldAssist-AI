from pydantic import BaseModel

class ChatInput(BaseModel):
    query: str
    category: str
    session_id: str | None = None