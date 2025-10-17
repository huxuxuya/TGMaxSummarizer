#!/usr/bin/env python3
"""
🖼️ Загрузка изображений из конкретного чата

Скрипт для загрузки всех изображений из выбранного чата VK MAX.
"""

import asyncio
import logging
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

async def download_chat_images(chat_title=None, days_back=7):
    """Загрузить изображения из конкретного чата"""
    logger.info("🖼️ ЗАГРУЗКА ИЗОБРАЖЕНИЙ ИЗ ЧАТА")
    logger.info("=" * 50)
    
    try:
        # Инициализация
        ctx = get_app_context()
        vk_client = VKMaxClient(ctx.config['bot'].vk_max_token)
        image_downloader = ImageDownloader()
        
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
        
        # Выбираем чат
        if chat_title:
            selected_chat = None
            for chat in chats:
                if chat_title.lower() in chat.title.lower():
                    selected_chat = chat
                    break
            
            if not selected_chat:
                logger.error(f"❌ Чат с названием '{chat_title}' не найден")
                logger.info("📝 Доступные чаты:")
                for i, chat in enumerate(chats):
                    logger.info(f"  {i+1}. {chat.title}")
                return
        else:
            # Берем первый чат
            selected_chat = chats[0]
        
        logger.info(f"🎯 Выбран чат: {selected_chat.title}")
        
        # Загружаем сообщения
        logger.info(f"📨 Загружаем сообщения за последние {days_back} дней...")
        messages = await vk_client.load_chat_messages(selected_chat.id, days_back=days_back)
        logger.info(f"✅ Загружено сообщений: {len(messages)}")
        
        # Статистика
        stats = {
            'messages_with_images': 0,
            'total_images': 0,
            'downloaded_images': 0,
            'errors': 0
        }
        
        # Обрабатываем сообщения
        for i, msg in enumerate(messages):
            # Проверяем attachments разными способами
            attachments = None
            if hasattr(msg, 'attachments') and msg.attachments:
                attachments = msg.attachments
            elif hasattr(msg, 'attaches') and msg.attaches:
                attachments = msg.attaches
            
            if attachments:
                try:
                    # Извлекаем URL изображений
                    image_urls = image_downloader.extract_image_urls(attachments)
                    
                    if image_urls:
                        stats['messages_with_images'] += 1
                        stats['total_images'] += len(image_urls)
                        
                        logger.info(f"📎 Сообщение {i+1}: найдено {len(image_urls)} изображений")
                        
                        # Скачиваем изображения
                        for j, url in enumerate(image_urls):
                            try:
                                saved_path = await image_downloader.download_image(
                                    url, str(selected_chat.id), str(msg.id), j
                                )
                                
                                if saved_path:
                                    stats['downloaded_images'] += 1
                                    logger.info(f"   ✅ Скачано: {saved_path}")
                                else:
                                    logger.warning(f"   ⚠️ Не удалось скачать изображение")
                                    
                            except Exception as e:
                                logger.error(f"   ❌ Ошибка скачивания: {e}")
                                stats['errors'] += 1
                
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки сообщения: {e}")
                    stats['errors'] += 1
        
        # Итоговая статистика
        logger.info("\n" + "=" * 50)
        logger.info("📊 ИТОГОВАЯ СТАТИСТИКА:")
        logger.info(f"   Обработано сообщений: {len(messages)}")
        logger.info(f"   Сообщений с изображениями: {stats['messages_with_images']}")
        logger.info(f"   Найдено изображений: {stats['total_images']}")
        logger.info(f"   Скачано изображений: {stats['downloaded_images']}")
        logger.info(f"   Ошибок: {stats['errors']}")
        
        if stats['total_images'] > 0:
            success_rate = (stats['downloaded_images'] / stats['total_images']) * 100
            logger.info(f"   Успешность: {success_rate:.1f}%")
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'vk_client' in locals():
            await vk_client.disconnect()
            logger.info("✅ Соединение закрыто")

async def main():
    """Главная функция"""
    # Можно указать название чата или оставить None для первого чата
    chat_title = None  # Например: "1.4_Лицей_ИТ"
    days_back = 7      # Количество дней для загрузки
    
    await download_chat_images(chat_title, days_back)

if __name__ == "__main__":
    asyncio.run(main())
