"""
Базовый абстрактный класс для AI провайдеров
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import logging
import asyncio
from datetime import datetime

from shared.utils import get_sender_display_name

logger = logging.getLogger(__name__)

class BaseAIProvider(ABC):
    """Абстрактный базовый класс для всех AI провайдеров"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация провайдера
        
        Args:
            config: Словарь с конфигурацией провайдера
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = self.get_name()
        self.is_initialized = False
        self.llm_logger = None
    
    @abstractmethod
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью данного провайдера
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
            
        Raises:
            Exception: При ошибке суммаризации
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Проверить доступность провайдера
        
        Returns:
            True если провайдер доступен, False иначе
        """
        pass
    
    @abstractmethod
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Генерировать ответ на произвольный промпт
        
        Args:
            prompt: Текст промпта для генерации ответа
            
        Returns:
            Сгенерированный ответ или None при ошибке
        """
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере
        
        Returns:
            Словарь с информацией о провайдере
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Валидация конфигурации провайдера
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        pass
    
    def get_name(self) -> str:
        """
        Получить имя провайдера
        
        Returns:
            Имя провайдера в нижнем регистре
        """
        return self.__class__.__name__.replace('Provider', '').lower()
    
    def get_display_name(self) -> str:
        """
        Получить отображаемое имя провайдера
        
        Returns:
            Человекочитаемое имя провайдера
        """
        name_mapping = {
            'gigachat': 'GigaChat',
            'chatgpt': 'ChatGPT',
            'openrouter': 'OpenRouter',
            'gemini': 'Gemini',
            'ollama': 'Ollama (Локальная)'
        }
        return name_mapping.get(self.name, self.name.title())
    
    async def initialize(self) -> bool:
        """
        Инициализация провайдера
        
        Returns:
            True если инициализация успешна, False иначе
        """
        try:
            if not self.validate_config():
                self.logger.error(f"❌ Неверная конфигурация для провайдера {self.name}")
                return False
            
            if not await self.is_available():
                self.logger.error(f"❌ Провайдер {self.name} недоступен")
                return False
            
            self.is_initialized = True
            self.logger.info(f"✅ Провайдер {self.name} успешно инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации провайдера {self.name}: {e}")
            return False
    
    def format_messages_for_analysis(self, messages: List[Dict]) -> str:
        """
        Форматирование сообщений для анализа
        
        Args:
            messages: Список сообщений
            
        Returns:
            Отформатированная строка для анализа
        """
        if not messages:
            return ""
        
        # Подсчитываем сообщения с анализом изображений
        messages_with_images = sum(1 for msg in messages if msg.get('image_analysis'))
        if messages_with_images > 0:
            self.logger.info(f"📸 Обнаружено {messages_with_images} сообщений с анализом изображений")
        
        formatted_lines = []
        for msg in messages:
            time_str = msg.get('time', '??:??')
            sender_id = msg.get('sender_id')
            
            # Используем новую функцию с ID и временем, но для Виктории Романовны оставляем как есть
            from shared.utils import get_sender_display_name_with_id
            sender = get_sender_display_name_with_id(
                sender_id,
                msg.get('sender', 'Неизвестно'),
                time_str
            )
            text = msg.get('text', '')
            
            # Получаем анализ изображений если он есть
            image_analysis = msg.get('image_analysis', [])
            
            if text.strip() or image_analysis:
                # Формируем основной текст сообщения (время уже включено в sender)
                line = f"{sender}:"
                
                # Добавляем текст сообщения
                if text.strip():
                    line += f" {text}"
                
                # Добавляем описание изображений
                if image_analysis and isinstance(image_analysis, list) and len(image_analysis) > 0:
                    for idx, analysis in enumerate(image_analysis, 1):
                        if isinstance(analysis, dict) and analysis.get('analysis'):
                            analysis_text = analysis['analysis']
                            if len(image_analysis) > 1:
                                line += f"\n  [Изображение {idx}]: {analysis_text}"
                            else:
                                line += f"\n  [Изображение]: {analysis_text}"
                
                formatted_lines.append(line)
        
        full_text = "\n".join(formatted_lines)
        
        # Ограничиваем длину текста для экономии токенов
        max_length = 8000
        if len(full_text) > max_length:
            full_text = full_text[:max_length] + "\n... (текст обрезан для экономии токенов)"
        
        return full_text
    
    def optimize_text(self, messages: List[Dict]) -> List[Dict]:
        """
        Оптимизация текста чата для передачи в языковую модель
        
        Args:
            messages: Список сообщений
            
        Returns:
            Оптимизированный список сообщений
        """
        import re
        optimized_messages = []
        
        for msg in messages:
            text = msg.get('text', '').strip()
            image_analysis = msg.get('image_analysis', [])
            
            # Пропускаем пустые сообщения БЕЗ изображений
            if not text and not image_analysis:
                continue
                
            # Убираем лишние символы из текста
            optimized_text = re.sub(r'\s+', ' ', text) if text else ''
            
            sender_id = msg.get('sender_id')
            sender_name = get_sender_display_name(
                sender_id,
                msg.get('sender_name', 'Неизвестно')
            )
            time = msg.get('message_time', 0)
            
            # Форматируем время
            if time:
                try:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(time / 1000)
                    time_str = dt.strftime('%H:%M')
                except (ValueError, OSError):
                    time_str = "??:??"
            else:
                time_str = "??:??"
            
            # Сохраняем image_analysis в оптимизированном сообщении
            optimized_msg = {
                'time': time_str,
                'sender_id': sender_id,
                'sender': sender_name,
                'text': optimized_text,
                'image_analysis': image_analysis  # Важно: сохраняем анализ изображений
            }
            
            optimized_messages.append(optimized_msg)
        
        return optimized_messages
    
    def __str__(self) -> str:
        """Строковое представление провайдера"""
        return f"{self.get_display_name()} Provider"
    
    def set_llm_logger(self, llm_logger):
        """
        Установить логгер для записи взаимодействий с LLM
        
        Args:
            llm_logger: Экземпляр LLMLogger
        """
        self.llm_logger = llm_logger
        self.logger.debug(f"📝 LLM Logger установлен для провайдера {self.name}")
    
    def __repr__(self) -> str:
        """Представление провайдера для отладки"""
        return f"{self.__class__.__name__}(name='{self.name}', initialized={self.is_initialized})"
