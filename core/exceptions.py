class BotException(Exception):
    """Базовое исключение бота"""
    pass

class ConfigurationError(BotException):
    """Ошибка конфигурации"""
    pass

class DatabaseError(BotException):
    """Ошибка базы данных"""
    pass

class AIProviderError(BotException):
    """Ошибка AI провайдера"""
    pass

class VKIntegrationError(BotException):
    """Ошибка интеграции с VK"""
    pass

class TelegramError(BotException):
    """Ошибка Telegram API"""
    pass

class ValidationError(BotException):
    """Ошибка валидации данных"""
    pass

