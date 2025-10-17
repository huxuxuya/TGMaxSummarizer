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
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="[%(asctime)s] [%(levelname)s] %(message)s")
    special_users: Dict[int, str] = Field(default_factory=dict)
    
    # Настройки анализа изображений
    ollama_base_url: str = Field(default="http://192.168.1.75:11434")
    default_image_analysis_model: str = Field(default="gemma3:27b")
    default_image_analysis_prompt: str = Field(default="Что изображено на этой картинке? Опиши подробно, что ты видишь.")
    image_analysis_max_concurrent: int = Field(default=5)
    
    def __init__(self, **data):
        super().__init__(**data)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token")
        self.vk_max_token = os.getenv("VK_MAX_TOKEN", "your_vk_max_token")
        self.max_message_length = int(os.getenv("MAX_MESSAGE_LENGTH", "4096"))
        self.max_messages_per_load = int(os.getenv("MAX_MESSAGES_PER_LOAD", "1000"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "[%(asctime)s] [%(levelname)s] %(message)s")
        
        # Настройки анализа изображений
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://192.168.1.75:11434")
        self.default_image_analysis_model = os.getenv("DEFAULT_IMAGE_ANALYSIS_MODEL", "gemma3:27b")
        self.default_image_analysis_prompt = os.getenv("DEFAULT_IMAGE_ANALYSIS_PROMPT", "Что изображено на этой картинке? Опиши подробно, что ты видишь.")
        self.image_analysis_max_concurrent = int(os.getenv("IMAGE_ANALYSIS_MAX_CONCURRENT", "5"))
        
        self.special_users = {
            44502596: "Виктория Романовна(учитель)"
        }

