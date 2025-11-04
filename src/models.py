import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime | None = None


class Document(BaseModel):
    file_path: Path
    file_name: str
    file_type: str
    text_content: str
    upload_date: datetime | None = None


class RetrievalResult(BaseModel):
    text: str
    distance: float
    similarity: float
    metadata: dict


class SupportTicket(BaseModel):
    ticket_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    customer_message: str
    status: str = "open"
    conversation_context: list[Message] | None = None
