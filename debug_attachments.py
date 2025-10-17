#!/usr/bin/env python3
"""
🔍 Отладка структуры attachments

Скрипт для детального анализа структуры attachments в сообщениях VK MAX.
"""

import asyncio
import logging
from core.app_context import get_app_context
from infrastructure.vk.client import VKMaxClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def debug_attachments():
    """Отладка структуры attachments"""
    logger.info("🔍 ОТЛАДКА СТРУКТУРЫ ATTACHMENTS")
    logger.info("=" * 50)
    
    try:
        # Инициализация
        ctx = get_app_context()
        vk_client = VKMaxClient(ctx.config['bot'].vk_max_token)
        
        # Подключаемся к VK MAX
        logger.info("🔗 Подключаемся к VK MAX...")
        if not await vk_client.connect():
            logger.error("❌ Не удалось подключиться к VK MAX")
            return
        
        # Получаем чаты
        logger.info("📋 Получаем список чатов...")
        chats = await vk_client.get_available_chats()
        
        if not chats:
            logger.error("❌ Чаты не найдены")
            return
        
        # Берем первый чат
        test_chat = chats[0]
        logger.info(f"🎯 Тестируем чат: {test_chat.title}")
        
        # Загружаем сообщения
        logger.info("📨 Загружаем сообщения...")
        messages = await vk_client.load_chat_messages(test_chat.id, days_back=7)
        logger.info(f"✅ Загружено сообщений: {len(messages)}")
        
        # Ищем сообщения с attachments
        found_attachments = False
        for i, msg in enumerate(messages[:50]):  # Проверяем первые 50 сообщений
            # Проверяем все возможные атрибуты
            attrs = dir(msg)
            attachment_attrs = [attr for attr in attrs if 'attach' in attr.lower()]
            
            if attachment_attrs:
                logger.info(f"📎 Сообщение {i+1}: найдены атрибуты: {attachment_attrs}")
                
                for attr in attachment_attrs:
                    value = getattr(msg, attr)
                    if value:
                        logger.info(f"   {attr}: {type(value)} = {value}")
                        found_attachments = True
                        
                        # Если это список, показываем первый элемент
                        if isinstance(value, list) and len(value) > 0:
                            logger.info(f"   Первый элемент {attr}: {value[0]}")
        
        if not found_attachments:
            logger.info("❌ Не найдено сообщений с attachments в первых 50 сообщениях")
            
            # Проверим все сообщения
            logger.info("🔍 Проверяем все сообщения...")
            total_with_attachments = 0
            for i, msg in enumerate(messages):
                attrs = dir(msg)
                attachment_attrs = [attr for attr in attrs if 'attach' in attr.lower()]
                
                for attr in attachment_attrs:
                    value = getattr(msg, attr)
                    if value:
                        total_with_attachments += 1
                        if total_with_attachments <= 3:  # Показываем первые 3
                            logger.info(f"📎 Сообщение {i+1}: {attr} = {value}")
                        break
            
            logger.info(f"📊 Всего сообщений с attachments: {total_with_attachments}")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'vk_client' in locals():
            await vk_client.disconnect()
            logger.info("✅ Соединение закрыто")

if __name__ == "__main__":
    asyncio.run(debug_attachments())
