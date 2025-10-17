"""
Фабрика для создания AI провайдеров
"""
from typing import Dict, List, Optional, Any
import logging
from .providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

class ProviderFactory:
    """Фабрика для создания и управления AI провайдерами"""
    
    # Реестр доступных провайдеров
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: type):
        """
        Регистрация нового провайдера
        
        Args:
            provider_type: Тип провайдера (например, 'gigachat')
            provider_class: Класс провайдера
        """
        if not issubclass(provider_class, BaseAIProvider):
            raise ValueError(f"Провайдер {provider_class} должен наследоваться от BaseAIProvider")
        
        cls._providers[provider_type.lower()] = provider_class
        logger.info(f"✅ Зарегистрирован провайдер: {provider_type}")
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any]) -> Optional[BaseAIProvider]:
        """
        Создать экземпляр провайдера
        
        Args:
            provider_type: Тип провайдера
            config: Конфигурация провайдера
            
        Returns:
            Экземпляр провайдера или None если тип не найден
        """
        provider_type = provider_type.lower()
        
        # Отладочная информация
        logger.debug(f"🔍 Создание провайдера {provider_type}, config type: {type(config)}, config: {config}")
        
        if provider_type not in cls._providers:
            logger.error(f"❌ Неизвестный тип провайдера: {provider_type}")
            return None
        
        try:
            provider_class = cls._providers[provider_type]
            provider = provider_class(config)
            logger.info(f"✅ Создан провайдер: {provider_type}")
            return provider
        except Exception as e:
            logger.error(f"❌ Ошибка создания провайдера {provider_type}: {e}")
            return None
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Получить список доступных провайдеров
        
        Returns:
            Список типов провайдеров
        """
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_available(cls, provider_type: str) -> bool:
        """
        Проверить доступность провайдера
        
        Args:
            provider_type: Тип провайдера
            
        Returns:
            True если провайдер доступен
        """
        return provider_type.lower() in cls._providers

# Автоматическая регистрация провайдеров при импорте
def _register_providers():
    """Регистрация всех доступных провайдеров"""
    try:
        from .providers.gigachat import GigaChatProvider
        from .providers.chatgpt import ChatGPTProvider
        from .providers.openrouter import OpenRouterProvider
        from .providers.gemini import GeminiProvider
        from .providers.ollama import OllamaProvider
        
        ProviderFactory.register_provider('gigachat', GigaChatProvider)
        ProviderFactory.register_provider('chatgpt', ChatGPTProvider)
        ProviderFactory.register_provider('openrouter', OpenRouterProvider)
        ProviderFactory.register_provider('gemini', GeminiProvider)
        ProviderFactory.register_provider('ollama', OllamaProvider)
        
        logger.info("✅ Все провайдеры зарегистрированы")
    except ImportError as e:
        logger.warning(f"⚠️ Не удалось зарегистрировать некоторые провайдеры: {e}")

# Регистрируем провайдеры при импорте модуля
_register_providers()