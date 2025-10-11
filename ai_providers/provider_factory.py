"""
Фабрика для создания AI провайдеров
"""
from typing import Dict, List, Optional, Any
import logging
from .base_provider import BaseAIProvider

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
            logger.error(f"🔍 Тип config: {type(config)}, значение: {config}")
            return None
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """
        Получить список доступных типов провайдеров
        
        Returns:
            Список типов провайдеров
        """
        return list(cls._providers.keys())
    
    @classmethod
    async def validate_all_providers(cls, config: Dict[str, Any]) -> Dict[str, bool]:
        """
        Валидация всех зарегистрированных провайдеров
        
        Args:
            config: Конфигурация для всех провайдеров
            
        Returns:
            Словарь с результатами валидации
        """
        results = {}
        
        for provider_type in cls._providers:
            try:
                provider = cls.create_provider(provider_type, config)
                if provider:
                    results[provider_type] = await provider.is_available()
                else:
                    results[provider_type] = False
            except Exception as e:
                logger.error(f"❌ Ошибка валидации провайдера {provider_type}: {e}")
                results[provider_type] = False
        
        return results
    
    @classmethod
    def get_provider_info(cls, provider_type: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о провайдере
        
        Args:
            provider_type: Тип провайдера
            config: Конфигурация провайдера
            
        Returns:
            Информация о провайдере или None
        """
        provider = cls.create_provider(provider_type, config)
        if provider:
            return provider.get_provider_info()
        return None
    
    @classmethod
    def get_all_providers_info(cls, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Получить информацию о всех провайдерах
        
        Args:
            config: Конфигурация для всех провайдеров
            
        Returns:
            Словарь с информацией о всех провайдерах
        """
        info = {}
        
        for provider_type in cls._providers:
            provider_info = cls.get_provider_info(provider_type, config)
            if provider_info:
                info[provider_type] = provider_info
        
        return info
    
    @classmethod
    async def get_best_available_provider(cls, config: Dict[str, Any], preferred_provider: Optional[str] = None) -> Optional[str]:
        """
        Получить лучший доступный провайдер
        
        Args:
            config: Конфигурация для всех провайдеров
            preferred_provider: Предпочитаемый провайдер
            
        Returns:
            Тип лучшего доступного провайдера или None
        """
        # Сначала проверяем предпочитаемый провайдер
        if preferred_provider:
            provider = cls.create_provider(preferred_provider, config)
            if provider and await provider.is_available():
                logger.info(f"✅ Используем предпочитаемый провайдер: {preferred_provider}")
                return preferred_provider
        
        # Проверяем все провайдеры
        validation_results = await cls.validate_all_providers(config)
        
        # Ищем первый доступный провайдер
        for provider_type, is_available in validation_results.items():
            if is_available:
                logger.info(f"✅ Используем доступный провайдер: {provider_type}")
                return provider_type
        
        logger.error("❌ Нет доступных провайдеров")
        return None
    
    @classmethod
    def is_provider_registered(cls, provider_type: str) -> bool:
        """
        Проверить, зарегистрирован ли провайдер
        
        Args:
            provider_type: Тип провайдера
            
        Returns:
            True если провайдер зарегистрирован, False иначе
        """
        return provider_type.lower() in cls._providers
    
    @classmethod
    def get_registered_providers_count(cls) -> int:
        """
        Получить количество зарегистрированных провайдеров
        
        Returns:
            Количество зарегистрированных провайдеров
        """
        return len(cls._providers)
    
    @classmethod
    def clear_registry(cls):
        """
        Очистить реестр провайдеров (для тестирования)
        """
        cls._providers.clear()
        logger.info("🧹 Реестр провайдеров очищен")
