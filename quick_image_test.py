#!/usr/bin/env python3
"""
⚡ Быстрый тест загрузки изображений из VK MAX

Простой скрипт для проверки работы загрузки изображений.
Запуск: python quick_image_test.py
"""

import asyncio
import logging
import json
from datetime import datetime

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

async def quick_test():
    """Быстрый тест загрузки изображений"""
    logger.info("⚡ Быстрый тест загрузки изображений")
    
    try:
        # Получаем контекст
        ctx = get_app_context()
        vk_token = ctx.config['bot'].vk_max_token
        
        if vk_token == "your_vk_max_token":
            logger.error("❌ VK MAX токен не установлен")
            return
        
        # Подключаемся к VK MAX
        logger.info("🔗 Подключаемся к VK MAX...")
        vk_client = VKMaxClient(vk_token)
        
        if not await vk_client.connect():
            logger.error("❌ Не удалось подключиться к VK MAX")
            return
        
        logger.info("✅ Подключение успешно")
        
        # Получаем чаты
        logger.info("📋 Получаем список чатов...")
        chats = await vk_client.get_available_chats()
        
        if not chats:
            logger.error("❌ Чаты не найдены")
            return
        
        logger.info(f"✅ Найдено {len(chats)} чатов")
        
        # Берем первый чат
        test_chat = chats[0]
        logger.info(f"🎯 Тестируем чат: {test_chat.title}")
        
        # Загружаем сообщения за последние 3 дня
        logger.info("📨 Загружаем сообщения...")
        messages = await vk_client.load_chat_messages(test_chat.id, days_back=3)
        
        logger.info(f"✅ Загружено {len(messages)} сообщений")
        
        # Ищем сообщения с изображениями
        image_downloader = ImageDownloader()
        messages_with_images = 0
        total_images = 0
        
        for msg in messages:
            if msg.attachments:
                messages_with_images += 1
                logger.info(f"📷 Сообщение {msg.id} содержит вложения:")
                logger.info(f"   Attachments: {json.dumps(msg.attachments, indent=2, ensure_ascii=False)}")
                
                # Извлекаем URL изображений
                image_urls = image_downloader.extract_image_urls(msg.attachments)
                logger.info(f"   Извлечено URL: {len(image_urls)}")
                
                for i, url in enumerate(image_urls):
                    logger.info(f"   URL {i+1}: {url}")
                    total_images += 1
                    
                    # Пробуем скачать
                    try:
                        saved_path = await image_downloader.download_image(
                            url, test_chat.id, msg.id, i
                        )
                        if saved_path:
                            logger.info(f"   ✅ Сохранено: {saved_path}")
                        else:
                            logger.warning(f"   ⚠️ Не удалось сохранить")
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка: {e}")
        
        logger.info(f"📊 Результат:")
        logger.info(f"   Сообщений с изображениями: {messages_with_images}")
        logger.info(f"   Всего изображений: {total_images}")
        
        # Отключаемся
        await vk_client.disconnect()
        logger.info("✅ Отключение от VK MAX")
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(quick_test())
