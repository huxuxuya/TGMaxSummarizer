import os
import aiohttp
import aiofiles
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class ImageDownloader:
    """Класс для скачивания и сохранения изображений из VK MAX"""
    
    def __init__(self, base_path: str = "images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Создаем подпапки для организации
        self.chat_images_path = self.base_path / "chats"
        self.chat_images_path.mkdir(exist_ok=True)
    
    def _get_image_extension(self, url: str, content_type: str = None) -> str:
        """Определить расширение файла изображения"""
        # Сначала пробуем из URL
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        if path.endswith(('.jpg', '.jpeg')):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        elif path.endswith('.webp'):
            return '.webp'
        
        # Если не удалось определить из URL, пробуем content-type
        if content_type:
            if 'jpeg' in content_type or 'jpg' in content_type:
                return '.jpg'
            elif 'png' in content_type:
                return '.png'
            elif 'gif' in content_type:
                return '.gif'
            elif 'webp' in content_type:
                return '.webp'
        
        # По умолчанию jpg
        return '.jpg'
    
    def _generate_filename(self, url: str, chat_id: str, message_id: str, index: int = 0) -> str:
        """Генерировать уникальное имя файла"""
        # Создаем хеш из URL для уникальности
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # Определяем расширение
        extension = self._get_image_extension(url)
        
        # Формат: chat_id_message_id_index_hash.extension
        filename = f"{chat_id}_{message_id}_{index}_{url_hash}{extension}"
        return filename
    
    async def download_image(self, url: str, chat_id: str, message_id: str, index: int = 0) -> Optional[str]:
        """Скачать изображение и вернуть путь к файлу"""
        try:
            # Создаем папку для чата
            chat_folder = self.chat_images_path / chat_id
            chat_folder.mkdir(exist_ok=True)
            
            # Генерируем имя файла
            filename = self._generate_filename(url, chat_id, message_id, index)
            file_path = chat_folder / filename
            
            # Проверяем, не скачан ли уже файл
            if file_path.exists():
                logger.info(f"🖼️ Изображение уже существует: {file_path}")
                return str(file_path.relative_to(self.base_path))
            
            # Скачиваем изображение
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        
                        # Проверяем, что это изображение
                        if not content_type.startswith('image/'):
                            logger.warning(f"⚠️ URL не является изображением: {url}")
                            return None
                        
                        # Обновляем расширение на основе content-type
                        extension = self._get_image_extension(url, content_type)
                        if not filename.endswith(extension):
                            filename = filename.rsplit('.', 1)[0] + extension
                            file_path = chat_folder / filename
                        
                        # Сохраняем файл
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"✅ Изображение сохранено: {file_path}")
                        return str(file_path.relative_to(self.base_path))
                    else:
                        logger.error(f"❌ Ошибка скачивания изображения {url}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Ошибка при скачивании изображения {url}: {e}")
            return None
    
    def extract_image_urls(self, attachments: List[Dict[str, Any]]) -> List[str]:
        """Извлечь URL изображений из вложений VK MAX"""
        image_urls = []
        
        for attachment in attachments:
            att_type = attachment.get("type", "").lower()
            data = attachment.get("data", {})
            
            if att_type == "photo":
                # Для фотографий ищем URL в разных возможных местах
                if isinstance(data, dict):
                    # Пробуем разные варианты URL
                    for url_key in ["url", "photo_url", "src", "src_big", "src_small"]:
                        if url_key in data and data[url_key]:
                            image_urls.append(data[url_key])
                            break
                    
                    # Если не нашли прямой URL, ищем в подструктурах
                    if not any(url_key in data for url_key in ["url", "photo_url", "src", "src_big", "src_small"]):
                        # Ищем в sizes или других структурах
                        if "sizes" in data and isinstance(data["sizes"], list):
                            for size in data["sizes"]:
                                if isinstance(size, dict) and "url" in size:
                                    image_urls.append(size["url"])
                                    break
                        
                        # Ищем в других возможных полях
                        for key, value in data.items():
                            if isinstance(value, str) and (value.startswith("http") and any(ext in value.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])):
                                image_urls.append(value)
                                break
            
            elif att_type in ["image", "picture"]:
                # Для других типов изображений
                if isinstance(data, dict) and "url" in data:
                    image_urls.append(data["url"])
        
        return image_urls
    
    async def process_message_images(self, attachments: List[Dict[str, Any]], chat_id: str, message_id: str) -> List[str]:
        """Обработать все изображения в сообщении и вернуть пути к файлам"""
        image_urls = self.extract_image_urls(attachments)
        saved_paths = []
        
        for i, url in enumerate(image_urls):
            saved_path = await self.download_image(url, chat_id, message_id, i)
            if saved_path:
                saved_paths.append(saved_path)
        
        return saved_paths
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """Получить информацию об изображении"""
        full_path = self.base_path / image_path
        
        if not full_path.exists():
            return {"exists": False}
        
        stat = full_path.stat()
        return {
            "exists": True,
            "size": stat.st_size,
            "path": str(full_path),
            "relative_path": image_path
        }
