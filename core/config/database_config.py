from .base import BaseConfig
from pydantic import Field
import os

class DatabaseConfig(BaseConfig):
    """Конфигурация базы данных"""
    
    path: str = Field(default="bot_database.db")
    chats_dir: str = Field(default="../chats")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.path = os.getenv("DATABASE_PATH", "bot_database.db")
        self.chats_dir = os.getenv("CHATS_DIR", "../chats")

