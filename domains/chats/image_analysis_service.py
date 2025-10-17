"""
Сервис для анализа изображений с помощью LLM через Ollama
"""

import asyncio
import base64
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import aiohttp

from .models import Message
from .repository import MessageRepository

logger = logging.getLogger(__name__)

class ImageAnalysisService:
    """Сервис для анализа изображений"""
    
    def __init__(self, 
                 ollama_base_url: str = "http://192.168.1.75:11434",
                 default_model: str = "gemma3:27b",
                 default_prompt: str = "Что изображено на этой картинке? Опиши подробно, что ты видишь.",
                 max_concurrent: int = 5):
        self.ollama_base_url = ollama_base_url
        self.default_model = default_model
        self.default_prompt = default_prompt
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_image(self, image_path: str, model: str = None, prompt: str = None) -> Optional[str]:
        """
        Анализировать одно изображение с помощью Ollama
        
        Args:
            image_path: Путь к изображению
            model: Модель для анализа (по умолчанию self.default_model)
            prompt: Промпт для анализа (по умолчанию self.default_prompt)
            
        Returns:
            Результат анализа или None в случае ошибки
        """
        if model is None:
            model = self.default_model
        if prompt is None:
            prompt = self.default_prompt
        
        # Проверяем существование файла
        # Если путь не начинается с images/, добавляем префикс
        if not image_path.startswith('images/'):
            image_path = f"images/{image_path}"
        
        image_file = Path(image_path)
        if not image_file.exists():
            logger.error(f"Файл изображения не найден: {image_path}")
            return None
        
        # Кодируем изображение в base64
        try:
            with open(image_file, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Ошибка при кодировании изображения {image_path}: {e}")
            return None
        
        # Подготавливаем данные для запроса
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=180  # Увеличиваем таймаут для больших изображений
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('response', '')
                    else:
                        logger.error(f"Ошибка API для {image_path}: HTTP {response.status}")
                        error_text = await response.text()
                        logger.error(f"Детали ошибки: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при анализе изображения {image_path}: {e}")
            return None
    
    async def analyze_message_images(self, message: Message, model: str = None, prompt: str = None) -> List[Dict[str, Any]]:
        """
        Анализировать все изображения в сообщении
        
        Args:
            message: Объект сообщения
            model: Модель для анализа
            prompt: Промпт для анализа
            
        Returns:
            Список результатов анализа для каждого изображения
        """
        if not message.image_paths:
            return []
        
        results = []
        analyzed_at = datetime.now().isoformat()
        
        # Создаем задачи для всех изображений
        tasks = []
        for image_path in message.image_paths:
            task = self._analyze_single_image_with_semaphore(
                image_path, model, prompt, analyzed_at
            )
            tasks.append(task)
        
        # Запускаем анализ всех изображений параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Фильтруем успешные результаты
        successful_results = []
        for result in results:
            if isinstance(result, dict) and result.get('analysis'):
                successful_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Ошибка при анализе изображения: {result}")
        
        return successful_results
    
    async def _analyze_single_image_with_semaphore(self, 
                                                  image_path: str, 
                                                  model: str, 
                                                  prompt: str, 
                                                  analyzed_at: str) -> Dict[str, Any]:
        """Анализировать одно изображение с семафором"""
        async with self.semaphore:
            analysis = await self.analyze_image(image_path, model, prompt)
            
            if analysis:
                return {
                    "image_path": image_path,
                    "analysis": analysis,
                    "analyzed_at": analyzed_at,
                    "model": model or self.default_model,
                    "prompt": prompt or self.default_prompt
                }
            else:
                return {
                    "image_path": image_path,
                    "analysis": None,
                    "analyzed_at": analyzed_at,
                    "model": model or self.default_model,
                    "prompt": prompt or self.default_prompt,
                    "error": "Не удалось проанализировать изображение"
                }
    
    async def get_unanalyzed_messages(self, vk_chat_id: str, repository: MessageRepository) -> List[Message]:
        """
        Получить сообщения с неанализированными изображениями
        
        Args:
            vk_chat_id: ID чата VK MAX
            repository: Репозиторий сообщений
            
        Returns:
            Список сообщений с изображениями, которые не были проанализированы
        """
        # Получаем все сообщения с изображениями
        messages_with_images = repository.get_messages_with_images(vk_chat_id)
        
        # Фильтруем сообщения без анализа
        unanalyzed = []
        for message in messages_with_images:
            if not message.image_analysis or len(message.image_analysis) == 0:
                unanalyzed.append(message)
            else:
                # Проверяем, что все изображения проанализированы
                analyzed_paths = {analysis.get('image_path') for analysis in message.image_analysis if analysis.get('analysis')}
                if len(analyzed_paths) < len(message.image_paths):
                    unanalyzed.append(message)
        
        return unanalyzed
    
    async def analyze_chat_images(self, 
                                 vk_chat_id: str, 
                                 repository: MessageRepository,
                                 model: str = None, 
                                 prompt: str = None,
                                 progress_callback: callable = None) -> Dict[str, Any]:
        """
        Анализировать все изображения в чате
        
        Args:
            vk_chat_id: ID чата VK MAX
            repository: Репозиторий сообщений
            model: Модель для анализа
            prompt: Промпт для анализа
            progress_callback: Функция для отслеживания прогресса
            
        Returns:
            Статистика анализа
        """
        # Получаем сообщения для анализа
        unanalyzed_messages = await self.get_unanalyzed_messages(vk_chat_id, repository)
        
        if not unanalyzed_messages:
            return {
                "total_messages": 0,
                "total_images": 0,
                "analyzed_images": 0,
                "failed_images": 0,
                "processing_time": 0
            }
        
        # Подсчитываем общее количество изображений
        total_images = sum(len(msg.image_paths) for msg in unanalyzed_messages)
        
        stats = {
            "total_messages": len(unanalyzed_messages),
            "total_images": total_images,
            "analyzed_images": 0,
            "failed_images": 0,
            "processing_time": 0
        }
        
        start_time = datetime.now()
        
        # Анализируем сообщения
        for i, message in enumerate(unanalyzed_messages):
            try:
                # Анализируем изображения в сообщении
                analysis_results = await self.analyze_message_images(message, model, prompt)
                
                # Обновляем сообщение в БД
                repository.update_message_analysis(message.message_id, analysis_results)
                
                # Обновляем статистику
                successful_analyses = [r for r in analysis_results if r.get('analysis')]
                stats["analyzed_images"] += len(successful_analyses)
                stats["failed_images"] += len(analysis_results) - len(successful_analyses)
                
                # Вызываем callback для прогресса
                if progress_callback:
                    await progress_callback(i + 1, len(unanalyzed_messages), stats)
                
            except Exception as e:
                logger.error(f"Ошибка при анализе сообщения {message.message_id}: {e}")
                stats["failed_images"] += len(message.image_paths)
        
        end_time = datetime.now()
        stats["processing_time"] = (end_time - start_time).total_seconds()
        
        return stats
    
    async def get_available_models(self) -> List[str]:
        """Получить список доступных моделей из Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model_info in data.get('models', []):
                            model_name = model_info.get('name', '')
                            if model_name:
                                models.append(model_name)
                        return models
                    else:
                        logger.error(f"Ошибка получения моделей: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Ошибка подключения к Ollama: {e}")
            return []
    
    async def analyze_schedule_photo(self, file_id: str, bot, model: str = None, prompt: str = None) -> Optional[str]:
        """
        Анализ фото расписания по file_id из Telegram
        
        Args:
            file_id: file_id фото из Telegram
            bot: экземпляр Telegram бота
            model: модель для анализа (по умолчанию self.default_model)
            prompt: промпт для анализа (по умолчанию специальный промпт для расписания)
            
        Returns:
            Результат анализа или None в случае ошибки
        """
        if model is None:
            model = self.default_model
        if prompt is None:
            prompt = "Распознай текст расписания занятий. Укажи все уроки, время и другую информацию. Опиши структуру расписания подробно."
        
        try:
            # Получаем файл от Telegram
            file = await bot.get_file(file_id)
            
            # Создаем временный файл
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_path = temp_file.name
            
            # Скачиваем файл
            await file.download_to_drive(temp_path)
            
            try:
                # Анализируем изображение
                result = await self.analyze_image(temp_path, model, prompt)
                return result
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Ошибка анализа фото расписания: {e}")
            return None
