from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ChatType(str, Enum):
    """Типы чатов"""
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"
    CHAT = "CHAT"
    UNKNOWN = "unknown"

class MessageType(str, Enum):
    """Типы сообщений"""
    USER = "USER"
    SYSTEM = "SYSTEM"
    BOT = "BOT"

class Chat(BaseModel):
    """Модель чата VK MAX"""
    chat_id: str
    chat_name: str
    chat_type: ChatType = ChatType.UNKNOWN
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Message(BaseModel):
    """Модель сообщения"""
    message_id: str
    vk_chat_id: str
    sender_id: Optional[int] = None
    sender_name: Optional[str] = None
    text: str = ""
    message_time: Optional[int] = None
    date: str = ""
    message_type: MessageType = MessageType.USER
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    reaction_info: Dict[str, Any] = Field(default_factory=dict)
    image_paths: List[str] = Field(default_factory=list)  # Пути к сохраненным изображениям
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChatStats(BaseModel):
    """Статистика чата"""
    vk_chat_id: str
    total_messages: int = 0
    days_count: int = 0
    recent_days: List[Dict[str, Any]] = Field(default_factory=list)

class Group(BaseModel):
    """Модель Telegram группы"""
    group_id: int
    group_name: str
    schedule_photo_file_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class GroupUser(BaseModel):
    """Связь пользователя с группой"""
    group_id: int
    user_id: int
    is_admin: bool = False

class GroupVKChat(BaseModel):
    """Связь группы с чатом VK MAX"""
    group_id: int
    vk_chat_id: str
    added_by: int
    added_at: Optional[datetime] = None

