#!/usr/bin/env python3
"""
🖼️ Загрузка всех изображений из VK MAX

Скрипт для загрузки всех изображений из всех доступных чатов VK MAX.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

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

class ImageDownloaderBot:
    """Бот для загрузки всех изображений из VK MAX"""
    
    def __init__(self):
        self.vk_client = None
        self.image_downloader = ImageDownloader()
        self.stats = {
            'chats_processed': 0,
            'messages_processed': 0,
            'images_found': 0,
            'images_downloaded': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Инициализация бота"""
        try:
            ctx = get_app_context()
            vk_token = ctx.config['bot'].vk_max_token
            
            if not vk_token:
                logger.error("❌ VK MAX токен не найден")
                return False
            
            self.vk_client = VKMaxClient(vk_token)
            
            # Подключаемся к VK MAX
            logger.info("🔗 Подключаемся к VK MAX...")
            if not await self.vk_client.connect():
                logger.error("❌ Не удалось подключиться к VK MAX")
                return False
            
            logger.info("✅ VK MAX клиент инициализирован и подключен")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            return False
    
    async def download_chat_images(self, chat, days_back=30):
        """Загрузить все изображения из чата"""
        logger.info(f"📨 Обрабатываем чат: {chat.title}")
        
        try:
            # Загружаем сообщения
            messages = await self.vk_client.load_chat_messages(chat.id, days_back=days_back)
            logger.info(f"   📥 Загружено сообщений: {len(messages)}")
            
            chat_images = 0
            
            # Обрабатываем каждое сообщение
            for msg in messages:
                self.stats['messages_processed'] += 1
                
                if hasattr(msg, 'attachments') and msg.attachments:
                    try:
                        # Извлекаем URL изображений
                        image_urls = self.image_downloader.extract_image_urls(msg.attachments)
                        
                        if image_urls:
                            self.stats['images_found'] += len(image_urls)
                            logger.info(f"   🖼️ Найдено изображений в сообщении {msg.id}: {len(image_urls)}")
                            
                            # Скачиваем каждое изображение
                            for i, url in enumerate(image_urls):
                                try:
                                    saved_path = await self.image_downloader.download_image(
                                        url, str(chat.id), str(msg.id), i
                                    )
                                    
                                    if saved_path:
                                        self.stats['images_downloaded'] += 1
                                        chat_images += 1
                                        logger.info(f"      ✅ Скачано: {saved_path}")
                                    else:
                                        logger.warning(f"      ⚠️ Не удалось скачать: {url}")
                                        
                                except Exception as e:
                                    logger.error(f"      ❌ Ошибка скачивания {url}: {e}")
                                    self.stats['errors'] += 1
                    
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка обработки сообщения {msg.id}: {e}")
                        self.stats['errors'] += 1
            
            logger.info(f"   📊 Изображений в чате: {chat_images}")
            return chat_images
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки чата {chat.title}: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def download_all_images(self, days_back=30):
        """Загрузить все изображения из всех чатов"""
        logger.info("🖼️ ЗАГРУЗКА ВСЕХ ИЗОБРАЖЕНИЙ ИЗ VK MAX")
        logger.info("=" * 60)
        
        if not await self.initialize():
            return
        
        try:
            # Получаем список чатов
            logger.info("📋 Получаем список чатов...")
            chats = await self.vk_client.get_available_chats()
            
            if not chats:
                logger.error("❌ Чаты не найдены")
                return
            
            logger.info(f"✅ Найдено чатов: {len(chats)}")
            
            # Показываем список чатов
            logger.info("📝 Список чатов:")
            for i, chat in enumerate(chats):
                logger.info(f"  {i+1}. {chat.title} (ID: {chat.id})")
            
            # Обрабатываем каждый чат
            total_images = 0
            for i, chat in enumerate(chats):
                logger.info(f"\n--- Чат {i+1}/{len(chats)} ---")
                chat_images = await self.download_chat_images(chat, days_back)
                total_images += chat_images
                self.stats['chats_processed'] += 1
            
            # Выводим итоговую статистику
            logger.info("\n" + "=" * 60)
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА:")
            logger.info(f"   Обработано чатов: {self.stats['chats_processed']}")
            logger.info(f"   Обработано сообщений: {self.stats['messages_processed']}")
            logger.info(f"   Найдено изображений: {self.stats['images_found']}")
            logger.info(f"   Скачано изображений: {self.stats['images_downloaded']}")
            logger.info(f"   Ошибок: {self.stats['errors']}")
            logger.info(f"   Успешность: {(self.stats['images_downloaded']/max(self.stats['images_found'], 1)*100):.1f}%")
            
            # Показываем размер папки с изображениями
            images_path = Path("images")
            if images_path.exists():
                total_size = sum(f.stat().st_size for f in images_path.rglob('*') if f.is_file())
                logger.info(f"   Общий размер: {total_size/1024/1024:.1f} MB")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.vk_client:
                await self.vk_client.disconnect()
                logger.info("✅ Соединение с VK MAX закрыто")

async def main():
    """Главная функция"""
    downloader = ImageDownloaderBot()
    
    # Можно изменить количество дней для загрузки
    days_back = 30  # Загружаем изображения за последние 30 дней
    
    logger.info(f"🎯 Загружаем изображения за последние {days_back} дней")
    
    await downloader.download_all_images(days_back)

if __name__ == "__main__":
    asyncio.run(main())
