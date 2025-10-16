"""
Централизованное логирование Telegram сообщений для отладки форматирования
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TelegramMessageLogger:
    """
    Класс для логирования всех Telegram сообщений в JSON файлы
    для отладки проблем с форматированием MarkdownV2
    """
    
    LOG_DIR = Path("telegram_messages")
    
    @classmethod
    def ensure_log_directory(cls) -> Path:
        """
        Создает папку для логов если она не существует
        
        Returns:
            Path: Путь к папке логов
        """
        cls.LOG_DIR.mkdir(exist_ok=True)
        return cls.LOG_DIR
    
    @classmethod
    def get_log_path(cls) -> Path:
        """
        Генерирует уникальный путь к файлу лога с timestamp
        
        Returns:
            Path: Путь к файлу лога
        """
        cls.ensure_log_directory()
        
        # Создаем timestamp с микросекундами для уникальности
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d-%H-%M-%S")
        microseconds = now.microsecond
        
        filename = f"{timestamp_str}-{microseconds:06d}.json"
        return cls.LOG_DIR / filename
    
    @classmethod
    def log_message(cls, metadata: Dict[str, Any]) -> Path:
        """
        Сохраняет метаданные сообщения в JSON файл
        
        Args:
            metadata: Словарь с метаданными сообщения
            
        Returns:
            Path: Путь к созданному файлу лога
        """
        log_path = cls.get_log_path()
        
        # Добавляем timestamp если его нет
        if 'timestamp' not in metadata:
            metadata['timestamp'] = datetime.now().isoformat()
        
        try:
            # Сохраняем JSON с отступами для читаемости
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📝 Telegram message logged: {log_path}")
            return log_path
            
        except Exception as e:
            logger.error(f"❌ Failed to log telegram message: {e}")
            raise
    
    @classmethod
    def update_log(cls, log_path: Path, updates: Dict[str, Any]) -> bool:
        """
        Обновляет существующий лог новыми данными
        
        Args:
            log_path: Путь к файлу лога
            updates: Словарь с обновлениями
            
        Returns:
            bool: True если обновление успешно, False иначе
        """
        try:
            # Читаем существующий лог
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Обновляем данные
            data.update(updates)
            
            # Добавляем timestamp обновления
            data['updated_at'] = datetime.now().isoformat()
            
            # Сохраняем обновленный лог
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📝 Telegram message log updated: {log_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update telegram message log {log_path}: {e}")
            return False
    
    @classmethod
    def log_success(cls, log_path: Path, message_id: Optional[int] = None) -> bool:
        """
        Обновляет лог при успешной отправке сообщения
        
        Args:
            log_path: Путь к файлу лога
            message_id: ID отправленного сообщения (если есть)
            
        Returns:
            bool: True если обновление успешно
        """
        updates = {
            'success': True,
            'completed_at': datetime.now().isoformat()
        }
        
        if message_id is not None:
            updates['message_id'] = message_id
        
        return cls.update_log(log_path, updates)
    
    @classmethod
    def log_error(cls, log_path: Path, error: str) -> bool:
        """
        Обновляет лог при ошибке отправки сообщения
        
        Args:
            log_path: Путь к файлу лога
            error: Текст ошибки
            
        Returns:
            bool: True если обновление успешно
        """
        updates = {
            'success': False,
            'error': str(error),
            'failed_at': datetime.now().isoformat()
        }
        
        return cls.update_log(log_path, updates)
    
    @classmethod
    def create_metadata(cls, 
                       chat_id: Optional[int] = None,
                       action: str = "send",
                       parse_mode: str = "MarkdownV2",
                       content_type: str = "FORMATTED",
                       original_text: str = "",
                       formatted_text: str = "") -> Dict[str, Any]:
        """
        Создает базовые метаданные для лога сообщения
        
        Args:
            chat_id: ID чата
            action: Действие (send/edit)
            parse_mode: Режим парсинга
            content_type: Тип контента
            original_text: Исходный текст
            formatted_text: Отформатированный текст
            
        Returns:
            Dict: Словарь с метаданными
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'chat_id': chat_id,
            'action': action,
            'parse_mode': parse_mode,
            'content_type': content_type,
            'original_text': original_text,
            'formatted_text': formatted_text,
            'success': None  # Будет обновлено после отправки
        }
