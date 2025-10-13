"""
Конфигурация для Telegram бота
"""
import os
from pathlib import Path

# Загружаем переменные из .env файла
def load_env():
    """Загрузить переменные из .env файла"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Загружаем переменные окружения
load_env()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token")
VK_MAX_TOKEN = os.getenv("VK_MAX_TOKEN", "your_vk_max_token")

# AI Provider Configuration
AI_PROVIDERS = {
    'gigachat': {
        'api_key': os.getenv("GIGACHAT_API_KEY", "your_gigachat_key"),
        'enabled': True,
        'display_name': 'GigaChat',
        'description': 'Sberbank GigaChat AI'
    },
    'chatgpt': {
        'api_key': os.getenv("OPENAI_API_KEY", "your_openai_key"),
        'enabled': True,
        'display_name': 'ChatGPT',
        'description': 'OpenAI ChatGPT'
    },
    'openrouter': {
        'api_key': os.getenv("OPENROUTER_API_KEY", "your_openrouter_key"),
        'enabled': True,
        'display_name': 'OpenRouter',
        'description': 'OpenRouter with DeepSeek'
    },
    'gemini': {
        'api_key': os.getenv("GEMINI_API_KEY", "your_gemini_key"),
        'enabled': True,
        'display_name': 'Gemini',
        'description': 'Google Gemini Pro'
    },
    'ollama': {
        'base_url': os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        'model': os.getenv("OLLAMA_MODEL", "gpt-oss:20b"),
        'timeout': int(os.getenv("OLLAMA_TIMEOUT", "120")),
        'enabled': True,
        'display_name': 'Ollama (Локальная)',
        'description': 'Локальная модель gpt-oss:20b через Ollama'
    }
}

# AI Provider Settings
DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "gigachat")
FALLBACK_PROVIDERS = os.getenv("FALLBACK_PROVIDERS", "chatgpt,gemini").split(',')
AI_PROVIDER_TIMEOUT = int(os.getenv("AI_PROVIDER_TIMEOUT", "30"))
AI_PROVIDER_MAX_RETRIES = int(os.getenv("AI_PROVIDER_MAX_RETRIES", "3"))

# Reflection Settings
ENABLE_REFLECTION = os.getenv("ENABLE_REFLECTION", "true").lower() == "true"
REFLECTION_TIMEOUT = int(os.getenv("REFLECTION_TIMEOUT", "60"))
AUTO_IMPROVE_SUMMARY = os.getenv("AUTO_IMPROVE_SUMMARY", "false").lower() == "true"

# Debug reflection settings
print(f"DEBUG: ENABLE_REFLECTION = {ENABLE_REFLECTION}")
print(f"DEBUG: AUTO_IMPROVE_SUMMARY = {AUTO_IMPROVE_SUMMARY}")

# Backward compatibility
GIGACHAT_API_KEY = AI_PROVIDERS['gigachat']['api_key']

# Database Configuration
DATABASE_PATH = "bot_database.db"
CHATS_DIR = "../chats"  # Путь к папке с файлами чатов

# Bot Settings
ADMIN_USER_IDS = []  # Список ID администраторов бота
MAX_MESSAGE_LENGTH = 4096  # Максимальная длина сообщения Telegram
MAX_MESSAGES_PER_LOAD = 1000  # Максимальное количество сообщений за одну загрузку

# Logging Configuration
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(message)s"

# LLM Logging Configuration
LLM_LOGS_DIR = os.getenv("LLM_LOGS_DIR", "llm_logs")
ENABLE_LLM_LOGGING = os.getenv("ENABLE_LLM_LOGGING", "true").lower() == "true"
LLM_LOGS_RETENTION_DAYS = int(os.getenv("LLM_LOGS_RETENTION_DAYS", "30"))
