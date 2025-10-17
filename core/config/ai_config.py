from .base import BaseConfig
from typing import Dict, List, Optional
from pydantic import Field, validator
import os

class AIProviderConfig(BaseConfig):
    """Конфигурация отдельного AI провайдера"""
    api_key: Optional[str] = None
    enabled: bool = True
    display_name: str
    description: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3

class AIConfig(BaseConfig):
    """Конфигурация AI провайдеров"""
    
    providers: Dict[str, AIProviderConfig] = Field(default_factory=dict)
    default_provider: str = Field(default="ollama")
    fallback_providers: List[str] = Field(default=["chatgpt", "gemini"])
    enable_reflection: bool = Field(default=True)
    auto_improve_summary: bool = Field(default=False)
    enable_llm_logging: bool = Field(default=True)
    llm_logs_dir: str = Field(default="llm_logs")
    llm_logs_retention_days: int = Field(default=30)
    
    def __init__(self, **data):
        super().__init__(**data)
        self._init_providers()
    
    def _init_providers(self):
        """Инициализация провайдеров из переменных окружения"""
        self.providers = {
            'gigachat': AIProviderConfig(
                api_key=os.getenv("GIGACHAT_API_KEY", "your_gigachat_key"),
                display_name='GigaChat',
                description='Sberbank GigaChat AI'
            ),
            'chatgpt': AIProviderConfig(
                api_key=os.getenv("OPENAI_API_KEY", "your_openai_key"),
                display_name='ChatGPT',
                description='OpenAI ChatGPT'
            ),
            'openrouter': AIProviderConfig(
                api_key=os.getenv("OPENROUTER_API_KEY", "your_openrouter_key"),
                display_name='OpenRouter',
                description='OpenRouter with DeepSeek'
            ),
            'gemini': AIProviderConfig(
                api_key=os.getenv("GEMINI_API_KEY", "your_gemini_key"),
                display_name='Gemini',
                description='Google Gemini Pro'
            ),
            'ollama': AIProviderConfig(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
                timeout=int(os.getenv("OLLAMA_TIMEOUT", "600")),
                display_name='Ollama (DeepSeek R1)',
                description='Локальная модель deepseek-r1:8b через Ollama'
            )
        }
        
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "ollama")
        self.fallback_providers = os.getenv("FALLBACK_PROVIDERS", "chatgpt,gemini").split(',')
        self.enable_reflection = os.getenv("ENABLE_REFLECTION", "true").lower() == "true"
        self.auto_improve_summary = os.getenv("AUTO_IMPROVE_SUMMARY", "false").lower() == "true"
        self.enable_llm_logging = os.getenv("ENABLE_LLM_LOGGING", "true").lower() == "true"
        self.llm_logs_dir = os.getenv("LLM_LOGS_DIR", "llm_logs")
        self.llm_logs_retention_days = int(os.getenv("LLM_LOGS_RETENTION_DAYS", "30"))
    
    @validator('default_provider')
    def validate_default_provider(cls, v, values):
        if 'providers' in values and v not in values['providers']:
            raise ValueError(f"Default provider '{v}' not found in providers")
        return v
    
    def get_provider_config(self, provider_name: str) -> Optional[AIProviderConfig]:
        """Получить конфигурацию провайдера"""
        return self.providers.get(provider_name)
    
    def get_available_providers(self) -> List[str]:
        """Получить список доступных провайдеров"""
        return [name for name, config in self.providers.items() if config.enabled]

