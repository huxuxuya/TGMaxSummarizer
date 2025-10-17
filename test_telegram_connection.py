#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к Telegram API
"""

import asyncio
import logging
from telegram import Bot
from core.config import load_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Тестирование подключения к Telegram API"""
    logger.info("🔍 Тестирование подключения к Telegram API...")
    
    # Загружаем конфигурацию
    config = load_config()
    token = config['bot'].telegram_bot_token
    
    if token == "your_bot_token":
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен")
        return False
    
    logger.info(f"✅ Токен загружен: {token[:10]}...{token[-10:]}")
    
    try:
        # Создаем бота
        bot = Bot(token=token)
        logger.info("✅ Объект Bot создан")
        
        # Тестируем подключение с коротким таймаутом
        logger.info("🔄 Тестирование get_me()...")
        me = await asyncio.wait_for(bot.get_me(), timeout=10)
        logger.info(f"✅ Подключение успешно: @{me.username} ({me.first_name})")
        
        # Тестируем получение обновлений
        logger.info("🔄 Тестирование get_updates()...")
        updates = await asyncio.wait_for(bot.get_updates(limit=1), timeout=10)
        logger.info(f"✅ Получение обновлений успешно: {len(updates)} обновлений")
        
        return True
        
    except asyncio.TimeoutError:
        logger.error("❌ Таймаут при подключении к Telegram API")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram API: {e}")
        return False

async def test_bot_initialization():
    """Тестирование инициализации бота"""
    logger.info("🔍 Тестирование инициализации бота...")
    
    try:
        from core.app_context import get_app_context
        from domains.handlers_manager import HandlersManager
        
        # Инициализация контекста
        ctx = get_app_context()
        logger.info("✅ AppContext инициализирован")
        
        # Инициализация обработчиков
        handlers = HandlersManager()
        logger.info("✅ HandlersManager инициализирован")
        
        # Создание приложения
        from telegram.ext import Application
        config = ctx.config
        
        app = Application.builder().token(
            config['bot'].telegram_bot_token
        ).connection_pool_size(8).read_timeout(30).write_timeout(30).connect_timeout(10).build()
        
        logger.info("✅ Application создано")
        
        # Инициализация приложения
        await app.initialize()
        logger.info("✅ Application инициализировано")
        
        # Запуск приложения
        await app.start()
        logger.info("✅ Application запущено")
        
        # Остановка приложения
        await app.stop()
        await app.shutdown()
        logger.info("✅ Application остановлено")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция"""
    logger.info("🧪 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К TELEGRAM")
    logger.info("=" * 50)
    
    # Тест 1: Подключение к API
    success1 = await test_telegram_connection()
    
    if success1:
        logger.info("\n" + "=" * 50)
        # Тест 2: Инициализация бота
        success2 = await test_bot_initialization()
        
        if success2:
            logger.info("\n" + "=" * 50)
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            logger.info("Бот должен запускаться без проблем.")
        else:
            logger.error("\n❌ Проблема с инициализацией бота")
    else:
        logger.error("\n❌ Проблема с подключением к Telegram API")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        logger.error(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
