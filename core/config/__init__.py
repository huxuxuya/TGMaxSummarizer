from .base import BaseConfig
from .ai_config import AIConfig
from .database_config import DatabaseConfig
from .bot_config import BotConfig
from typing import Dict, Any
import os
from pathlib import Path

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

def load_config() -> Dict[str, Any]:
    """Загрузить всю конфигурацию"""
    load_env()
    
    return {
        'ai': AIConfig(),
        'database': DatabaseConfig(),
        'bot': BotConfig()
    }

