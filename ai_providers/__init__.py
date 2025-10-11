"""
Пакет AI провайдеров для VK MAX Telegram Bot
"""

from .base_provider import BaseAIProvider
from .provider_factory import ProviderFactory

# Импортируем провайдеры для автоматической регистрации
try:
    from .gigachat_provider import GigaChatProvider
    ProviderFactory.register_provider('gigachat', GigaChatProvider)
except ImportError as e:
    print(f"⚠️ Не удалось загрузить GigaChat провайдер: {e}")

try:
    from .chatgpt_provider import ChatGPTProvider
    ProviderFactory.register_provider('chatgpt', ChatGPTProvider)
except ImportError as e:
    print(f"⚠️ Не удалось загрузить ChatGPT провайдер: {e}")

try:
    from .openrouter_provider import OpenRouterProvider
    ProviderFactory.register_provider('openrouter', OpenRouterProvider)
except ImportError as e:
    print(f"⚠️ Не удалось загрузить OpenRouter провайдер: {e}")

try:
    from .gemini_provider import GeminiProvider
    ProviderFactory.register_provider('gemini', GeminiProvider)
except ImportError as e:
    print(f"⚠️ Не удалось загрузить Gemini провайдер: {e}")

__all__ = [
    'BaseAIProvider',
    'ProviderFactory',
    'GigaChatProvider',
    'ChatGPTProvider', 
    'OpenRouterProvider',
    'GeminiProvider'
]

__version__ = '1.0.0'
__author__ = 'VK MAX Telegram Bot Team'
