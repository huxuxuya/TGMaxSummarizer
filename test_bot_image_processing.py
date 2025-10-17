#!/usr/bin/env python3
"""
🤖 Тест обработки изображений в боте

Скрипт для тестирования логики обработки изображений,
которая используется в боте при загрузке сообщений.
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

async def test_bot_image_processing():
    """Тестируем обработку изображений как в боте"""
    logger.info("🤖 ТЕСТ ОБРАБОТКИ ИЗОБРАЖЕНИЙ В БОТЕ")
    logger.info("=" * 50)
    
    try:
        # Инициализация как в боте
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
        logger.info(f"🎯 Тестируем чат: {test_chat.title} (ID: {test_chat.id})")
        
        # Загружаем небольшое количество сообщений
        logger.info("📥 Загружаем сообщения...")
        messages = await vk_client.load_chat_messages(test_chat.id, days_back=1)
        logger.info(f"✅ Загружено сообщений: {len(messages)}")
        
        # Обрабатываем сообщения как в боте
        logger.info("🔄 Обрабатываем сообщения через format_messages_for_db...")
        formatted_messages = await vk_client.format_messages_for_db(messages, test_chat.id)
        
        # Анализируем результаты
        messages_with_images = 0
        total_images = 0
        
        for msg in formatted_messages:
            if msg.get('image_paths'):
                messages_with_images += 1
                total_images += len(msg['image_paths'])
                logger.info(f"📎 Сообщение {msg['message_id']}: {len(msg['image_paths'])} изображений")
                for i, path in enumerate(msg['image_paths']):
                    logger.info(f"   🖼️ {i+1}. {path}")
        
        logger.info("\n" + "=" * 50)
        logger.info("📊 РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        logger.info(f"   Обработано сообщений: {len(formatted_messages)}")
        logger.info(f"   Сообщений с изображениями: {messages_with_images}")
        logger.info(f"   Всего изображений: {total_images}")
        
        if messages_with_images > 0:
            logger.info("✅ Изображения успешно обработаны в боте!")
        else:
            logger.info("ℹ️ В загруженных сообщениях не найдено изображений")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'vk_client' in locals():
            await vk_client.disconnect()
            logger.info("✅ Соединение закрыто")

if __name__ == "__main__":
    asyncio.run(test_bot_image_processing())
