#!/usr/bin/env python3
"""
🔍 Отладка извлечения изображений из VK MAX

Скрипт для детального анализа процесса извлечения URL изображений.
"""

import asyncio
import logging
from core.app_context import get_app_context
from infrastructure.vk.client import VKMaxClient
from shared.image_utils import ImageDownloader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def debug_image_extraction():
    """Отладка извлечения изображений"""
    logger.info("🔍 ОТЛАДКА ИЗВЛЕЧЕНИЯ ИЗОБРАЖЕНИЙ")
    logger.info("=" * 50)
    
    try:
        # Получаем контекст
        ctx = get_app_context()
        vk_token = ctx.config['bot'].vk_max_token
        
        if not vk_token:
            logger.error("❌ VK MAX токен не найден")
            return
        
        # Создаем клиенты
        vk_client = VKMaxClient(vk_token)
        image_downloader = ImageDownloader()
        
        # Получаем чаты
        logger.info("📋 Получаем список чатов...")
        chats = await vk_client.get_available_chats()
        
        if not chats:
            logger.error("❌ Чаты не найдены")
            return
        
        logger.info(f"✅ Найдено чатов: {len(chats)}")
        
        # Берем первый чат
        test_chat = chats[0]
        logger.info(f"🎯 Тестируем чат: {test_chat.title}")
        
        # Загружаем сообщения
        logger.info("📨 Загружаем сообщения...")
        messages = await vk_client.load_chat_messages(test_chat.id, days_back=3)
        logger.info(f"✅ Загружено сообщений: {len(messages)}")
        
        # Ищем сообщения с attachments
        messages_with_attachments = []
        for msg in messages:
            if hasattr(msg, 'attachments') and msg.attachments:
                messages_with_attachments.append(msg)
        
        logger.info(f"📎 Найдено сообщений с attachments: {len(messages_with_attachments)}")
        
        if not messages_with_attachments:
            logger.warning("⚠️ Сообщений с attachments не найдено")
            return
        
        # Анализируем первые несколько сообщений с attachments
        for i, msg in enumerate(messages_with_attachments[:3]):
            logger.info(f"\n--- Сообщение {i+1} ---")
            logger.info(f"ID: {msg.id}")
            logger.info(f"Text: {msg.text[:100]}..." if msg.text else "Text: (пусто)")
            logger.info(f"Attachments type: {type(msg.attachments)}")
            logger.info(f"Attachments: {msg.attachments}")
            
            # Пробуем извлечь URL изображений
            try:
                image_urls = image_downloader.extract_image_urls(msg.attachments)
                logger.info(f"🖼️ Извлечено URL изображений: {len(image_urls)}")
                for j, url in enumerate(image_urls):
                    logger.info(f"  {j+1}. {url}")
            except Exception as e:
                logger.error(f"❌ Ошибка при извлечении URL: {e}")
        
        # Статистика
        total_images = 0
        for msg in messages_with_attachments:
            try:
                image_urls = image_downloader.extract_image_urls(msg.attachments)
                total_images += len(image_urls)
            except:
                pass
        
        logger.info(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   Сообщений с attachments: {len(messages_with_attachments)}")
        logger.info(f"   Всего изображений: {total_images}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_image_extraction())
