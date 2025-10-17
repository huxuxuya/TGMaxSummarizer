#!/usr/bin/env python3
"""
🧪 Тестовый скрипт для загрузки изображений из VK MAX

Этот скрипт:
1. Подключается к VK MAX
2. Получает список чатов
3. Загружает сообщения из выбранного чата
4. Сохраняет изображения локально
5. Показывает статистику

Запуск: python test_image_download.py
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

from core.app_context import get_app_context
from infrastructure.vk.client import VKMaxClient
from shared.image_utils import ImageDownloader
from shared.image_viewer import ImageViewer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ImageDownloadTester:
    """Тестер загрузки изображений"""
    
    def __init__(self):
        self.ctx = get_app_context()
        self.vk_client = None
        self.image_downloader = ImageDownloader()
        self.image_viewer = ImageViewer()
    
    async def run_test(self):
        """Запустить тест загрузки изображений"""
        logger.info("🧪 Начинаем тест загрузки изображений из VK MAX")
        
        try:
            # 1. Подключаемся к VK MAX
            await self._connect_to_vk_max()
            
            # 2. Получаем список чатов
            chats = await self._get_chats()
            if not chats:
                logger.error("❌ Не удалось получить список чатов")
                return
            
            # 3. Выбираем чат для тестирования
            test_chat = await self._select_test_chat(chats)
            if not test_chat:
                logger.error("❌ Не выбран чат для тестирования")
                return
            
            # 4. Загружаем сообщения
            messages = await self._load_messages(test_chat)
            if not messages:
                logger.error("❌ Не удалось загрузить сообщения")
                return
            
            # 5. Анализируем сообщения с изображениями
            await self._analyze_messages_with_images(messages, test_chat)
            
            # 6. Показываем статистику
            await self._show_statistics()
            
        except Exception as e:
            logger.error(f"❌ Ошибка в тесте: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.vk_client:
                await self.vk_client.disconnect()
    
    async def _connect_to_vk_max(self):
        """Подключиться к VK MAX"""
        logger.info("🔗 Подключаемся к VK MAX...")
        
        vk_token = self.ctx.config['bot'].vk_max_token
        if vk_token == "your_vk_max_token":
            raise ValueError("❌ VK MAX токен не установлен")
        
        self.vk_client = VKMaxClient(vk_token)
        success = await self.vk_client.connect()
        
        if not success:
            raise ConnectionError("❌ Не удалось подключиться к VK MAX")
        
        logger.info("✅ Подключение к VK MAX успешно")
    
    async def _get_chats(self):
        """Получить список чатов"""
        logger.info("📋 Получаем список чатов...")
        
        chats = await self.vk_client.get_available_chats()
        logger.info(f"✅ Найдено {len(chats)} чатов")
        
        for i, chat in enumerate(chats[:5]):  # Показываем первые 5
            logger.info(f"  {i+1}. {chat.title} (ID: {chat.id})")
        
        return chats
    
    async def _select_test_chat(self, chats):
        """Выбрать чат для тестирования"""
        if not chats:
            return None
        
        # Берем первый чат для тестирования
        test_chat = chats[0]
        logger.info(f"🎯 Выбран чат для тестирования: {test_chat.title} (ID: {test_chat.id})")
        return test_chat
    
    async def _load_messages(self, chat):
        """Загрузить сообщения из чата"""
        logger.info(f"📨 Загружаем сообщения из чата {chat.title}...")
        
        # Загружаем сообщения за последние 7 дней
        messages = await self.vk_client.load_chat_messages(chat.id, days_back=7)
        logger.info(f"✅ Загружено {len(messages)} сообщений")
        
        return messages
    
    async def _analyze_messages_with_images(self, messages, chat):
        """Анализировать сообщения с изображениями"""
        logger.info("🔍 Анализируем сообщения с изображениями...")
        
        messages_with_images = 0
        total_images = 0
        downloaded_images = 0
        
        for msg in messages:
            if msg.attachments:
                messages_with_images += 1
                logger.info(f"📷 Сообщение {msg.id} содержит {len(msg.attachments)} вложений")
                
                # Показываем структуру attachments
                logger.info(f"   Attachments: {json.dumps(msg.attachments, indent=2, ensure_ascii=False)}")
                
                # Извлекаем URL изображений
                image_urls = self.image_downloader.extract_image_urls(msg.attachments)
                logger.info(f"   Извлечено URL изображений: {len(image_urls)}")
                
                for i, url in enumerate(image_urls):
                    logger.info(f"   URL {i+1}: {url}")
                    total_images += 1
                    
                    # Скачиваем изображение
                    try:
                        saved_path = await self.image_downloader.download_image(
                            url, chat.id, msg.id, i
                        )
                        if saved_path:
                            downloaded_images += 1
                            logger.info(f"   ✅ Изображение сохранено: {saved_path}")
                        else:
                            logger.warning(f"   ⚠️ Не удалось сохранить изображение")
                    except Exception as e:
                        logger.error(f"   ❌ Ошибка скачивания: {e}")
        
        logger.info(f"📊 Статистика:")
        logger.info(f"   Сообщений с изображениями: {messages_with_images}")
        logger.info(f"   Всего изображений найдено: {total_images}")
        logger.info(f"   Успешно скачано: {downloaded_images}")
    
    async def _show_statistics(self):
        """Показать статистику изображений"""
        logger.info("📈 Статистика изображений:")
        
        try:
            stats = self.image_viewer.get_image_stats()
            logger.info(f"   Всего изображений в системе: {stats.get('total_images', 0)}")
            logger.info(f"   Чатов с изображениями: {stats.get('chats_with_images', 0)}")
            logger.info(f"   Общий размер: {stats.get('total_size_mb', 0):.2f} MB")
            
            # Показываем структуру папок
            images_path = Path("images")
            if images_path.exists():
                logger.info(f"   Папка изображений: {images_path.absolute()}")
                
                for chat_folder in images_path.glob("chats/*"):
                    if chat_folder.is_dir():
                        image_count = len(list(chat_folder.glob("*")))
                        logger.info(f"   📁 {chat_folder.name}: {image_count} изображений")
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")

async def main():
    """Главная функция"""
    print("🧪 ТЕСТ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ ИЗ VK MAX")
    print("=" * 50)
    
    tester = ImageDownloadTester()
    await tester.run_test()
    
    print("\n🎉 Тест завершен!")

if __name__ == "__main__":
    asyncio.run(main())
