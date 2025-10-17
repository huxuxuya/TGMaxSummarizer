from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class VKChat(BaseModel):
    """Модель чата VK MAX"""
    id: str
    title: str
    type: str = "UNKNOWN"
    participants_count: int = 0
    description: str = ""

class VKMessage(BaseModel):
    """Модель сообщения VK MAX"""
    id: Optional[str] = None
    message_id: Optional[str] = None
    sender: Optional[int] = None
    text: str = ""
    time: Optional[int] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    reactions: Dict[str, Any] = Field(default_factory=dict)
    elements: List[Dict[str, Any]] = Field(default_factory=list)

class VKUser(BaseModel):
    """Модель пользователя VK MAX"""
    id: int
    name: str

