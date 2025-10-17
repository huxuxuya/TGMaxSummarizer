from .base import BaseConfig
from typing import List, Dict
from pydantic import Field
import os

class BotConfig(BaseConfig):
    """Конфигурация Telegram бота"""
    
    telegram_bot_token: str = Field(default="your_bot_token")
    vk_max_token: str = Field(default="your_vk_max_token")
    admin_user_ids: List[int] = Field(default_factory=list)
    max_message_length: int = Field(default=4096)
    max_messages_per_load: int = Field(default=1000)
    log_level: str = Field(default="DEBUG")
    log_format: str = Field(default="[%(asctime)s] [%(levelname)s] %(message)s")
    special_users: Dict[int, str] = Field(default_factory=dict)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token")
        self.vk_max_token = os.getenv("VK_MAX_TOKEN", "your_vk_max_token")
        self.max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
        self.max_messages_per_load = int(os.getenv("MAX_MESSAGES_PER_LOAD", "1000"))
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG")
        self.log_format = os.getenv("LOG_FORMAT", "[%(asctime)s] [%(levelname)s] %(message)s")
        
        self.special_users = {
            44502596: "Виктория Романовна(учитель)"
        }

