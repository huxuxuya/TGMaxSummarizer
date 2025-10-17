import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from shared.image_utils import ImageDownloader

logger = logging.getLogger(__name__)

class ImageViewer:
    """Класс для просмотра и управления сохраненными изображениями"""
    
    def __init__(self, base_path: str = "images"):
        self.base_path = Path(base_path)
        self.image_downloader = ImageDownloader(base_path)
    
    def get_chat_images(self, chat_id: str) -> List[Dict[str, Any]]:
        """Получить все изображения для чата"""
        chat_folder = self.image_downloader.chat_images_path / chat_id
        
        if not chat_folder.exists():
            return []
        
        images = []
        for image_file in chat_folder.iterdir():
            if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                image_info = self.image_downloader.get_image_info(str(image_file.relative_to(self.base_path)))
                if image_info['exists']:
                    images.append({
                        'filename': image_file.name,
                        'path': str(image_file.relative_to(self.base_path)),
                        'size': image_info['size'],
                        'full_path': str(image_file)
                    })
        
        # Сортируем по имени файла (которое содержит timestamp)
        images.sort(key=lambda x: x['filename'])
        return images
    
    def get_message_images(self, chat_id: str, message_id: str) -> List[Dict[str, Any]]:
        """Получить изображения для конкретного сообщения"""
        chat_folder = self.image_downloader.chat_images_path / chat_id
        
        if not chat_folder.exists():
            return []
        
        images = []
        for image_file in chat_folder.iterdir():
            if image_file.is_file() and image_file.name.startswith(f"{chat_id}_{message_id}_"):
                image_info = self.image_downloader.get_image_info(str(image_file.relative_to(self.base_path)))
                if image_info['exists']:
                    images.append({
                        'filename': image_file.name,
                        'path': str(image_file.relative_to(self.base_path)),
                        'size': image_info['size'],
                        'full_path': str(image_file)
                    })
        
        # Сортируем по индексу в имени файла
        images.sort(key=lambda x: x['filename'])
        return images
    
    def get_image_stats(self) -> Dict[str, Any]:
        """Получить статистику по изображениям"""
        total_images = 0
        total_size = 0
        chats_count = 0
        
        if not self.image_downloader.chat_images_path.exists():
            return {
                'total_images': 0,
                'total_size': 0,
                'chats_count': 0,
                'size_mb': 0
            }
        
        for chat_folder in self.image_downloader.chat_images_path.iterdir():
            if chat_folder.is_dir():
                chats_count += 1
                for image_file in chat_folder.iterdir():
                    if image_file.is_file() and image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        total_images += 1
                        total_size += image_file.stat().st_size
        
        return {
            'total_images': total_images,
            'total_size': total_size,
            'chats_count': chats_count,
            'chats_with_images': chats_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'size_mb': round(total_size / (1024 * 1024), 2)
        }
    
    def get_all_images(self) -> Dict[str, List[Dict[str, Any]]]:
        """Получить все изображения по чатам"""
        all_images = {}
        
        if not self.image_downloader.chat_images_path.exists():
            return all_images
        
        for chat_folder in self.image_downloader.chat_images_path.iterdir():
            if chat_folder.is_dir():
                chat_id = chat_folder.name
                images = self.get_chat_images(chat_id)
                if images:
                    all_images[chat_id] = images
        
        return all_images
    
    def cleanup_orphaned_images(self, chat_id: str, valid_message_ids: List[str]) -> int:
        """Удалить изображения для несуществующих сообщений"""
        chat_folder = self.image_downloader.chat_images_path / chat_id
        
        if not chat_folder.exists():
            return 0
        
        removed_count = 0
        for image_file in chat_folder.iterdir():
            if image_file.is_file():
                # Извлекаем message_id из имени файла
                filename_parts = image_file.name.split('_')
                if len(filename_parts) >= 3:
                    file_message_id = filename_parts[1]
                    if file_message_id not in valid_message_ids:
                        try:
                            image_file.unlink()
                            removed_count += 1
                            logger.info(f"🗑️ Удален файл изображения: {image_file.name}")
                        except Exception as e:
                            logger.error(f"❌ Ошибка удаления файла {image_file.name}: {e}")
        
        return removed_count
    
    def format_image_info_for_telegram(self, images: List[Dict[str, Any]]) -> str:
        """Форматировать информацию об изображениях для Telegram"""
        if not images:
            return "🖼️ Изображения не найдены"
        
        text = f"🖼️ Найдено изображений: {len(images)}\n\n"
        
        for i, img in enumerate(images[:5], 1):  # Показываем только первые 5
            size_kb = round(img['size'] / 1024, 1)
            text += f"{i}. {img['filename']}\n"
            text += f"   📁 {img['path']}\n"
            text += f"   📏 {size_kb} KB\n\n"
        
        if len(images) > 5:
            text += f"... и еще {len(images) - 5} изображений"
        
        return text
