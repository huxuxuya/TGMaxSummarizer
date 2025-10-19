"""
Централизованное логирование Telegram сообщений для отладки форматирования
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from telegram import Update

logger = logging.getLogger(__name__)

class TelegramMessageLogger:
    """
    Класс для логирования всех Telegram сообщений (входящих и исходящих)
    """
    
    LOG_DIR = Path("message_logs")
    
    @classmethod
    def is_logging_enabled(cls, direction: str = None) -> bool:
        """
        Проверить, включено ли логирование
        
        Args:
            direction: 'incoming' или 'outgoing' (если None - общая проверка)
            
        Returns:
            bool: True если логирование включено
        """
        try:
            from core.app_context import get_app_context
            ctx = get_app_context()
            config = ctx.config['bot']
            
            if not config.enable_message_logging:
                return False
            
            if direction == 'incoming':
                return config.message_log_incoming
            elif direction == 'outgoing':
                return config.message_log_outgoing
            else:
                return True
                
        except Exception:
            # Если ошибка доступа к конфигу - не логируем
            return False
    
    @classmethod
    def get_log_path(cls, direction: str, chat_id: int) -> Path:
        """
        Генерирует путь к файлу лога с учетом направления, даты и типа чата
        
        Args:
            direction: 'incoming' или 'outgoing'
            chat_id: ID чата
            
        Returns:
            Path: Путь к файлу лога
        """
        # Создаем структуру: message_logs/incoming|outgoing/YYYY-MM-DD/
        now = datetime.now()
        date_folder = now.strftime("%Y-%m-%d")
        log_folder = cls.LOG_DIR / direction / date_folder
        log_folder.mkdir(parents=True, exist_ok=True)
        
        # Определяем префикс по типу чата
        chat_prefix = "group" if chat_id < 0 else "user"
        
        # Генерируем имя файла
        timestamp_str = now.strftime("%H-%M-%S")
        microseconds = now.microsecond
        
        filename = f"{chat_prefix}_{abs(chat_id)}_{timestamp_str}-{microseconds:06d}.json"
        return log_folder / filename
    
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
    def get_legacy_log_path(cls) -> Path:
        """
        Генерирует уникальный путь к файлу лога с timestamp (старый формат)
        
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
        log_path = cls.get_legacy_log_path()
        
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
    def log_incoming_message(cls,
                            update: Update,
                            **kwargs) -> Optional[Path]:
        """
        Логирует входящее сообщение
        
        Args:
            update: Update объект от Telegram
            **kwargs: Дополнительные параметры
            
        Returns:
            Path: Путь к файлу лога или None если логирование отключено
        """
        if not cls.is_logging_enabled('incoming'):
            return None
        
        try:
            message = update.effective_message
            user = update.effective_user
            chat = update.effective_chat
            
            # Определяем тип входящего сообщения
            is_callback = update.callback_query is not None
            
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'direction': 'incoming',
                'user_id': user.id if user else None,
                'username': user.username if user else None,
                'first_name': user.first_name if user else None,
                'last_name': user.last_name if user else None,
                'chat_id': chat.id,
                'chat_type': chat.type,
                'message_id': message.message_id if message else None,
                'text': None,  # Будет заполнено ниже
                'caption': None,  # Будет заполнено ниже
                'has_photo': bool(message and message.photo),
                'has_document': bool(message and message.document),
                'has_video': bool(message and message.video),
                'has_audio': bool(message and message.audio),
                'command': None,
                'callback_data': None
            }
            
            # Заполняем данные в зависимости от типа сообщения
            if is_callback:
                # Для callback queries логируем только callback_data, не текст сообщения
                metadata['callback_data'] = update.callback_query.data
                metadata['text'] = None  # Не логируем текст для callback queries
            else:
                # Для обычных сообщений логируем текст
                metadata['text'] = message.text if message and message.text else None
                metadata['caption'] = message.caption if message and message.caption else None
                
                # Если это команда
                if message and message.text and message.text.startswith('/'):
                    metadata['command'] = message.text.split()[0]
            
            # Добавляем дополнительные параметры
            for key, value in kwargs.items():
                if key not in metadata:
                    metadata[key] = value
            
            log_path = cls.get_log_path('incoming', chat.id)
            
            # Сохраняем лог
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📥 Incoming message logged: {log_path}")
            return log_path
            
        except Exception as e:
            logger.error(f"❌ Failed to log incoming message: {e}")
            return None
    
    @classmethod
    def log_outgoing_message(cls,
                            chat_id: int,
                            text: str,
                            action: str = "send",
                            parse_mode: str = "Markdown",
                            context: Optional[Dict[str, Any]] = None,
                            **kwargs) -> Optional[Path]:
        """
        Логирует исходящее сообщение с полным контекстом
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
            action: Действие (send/edit)
            parse_mode: Режим парсинга
            context: Дополнительный контекст
            **kwargs: Дополнительные параметры
            
        Returns:
            Path: Путь к файлу лога или None если логирование отключено
        """
        if not cls.is_logging_enabled('outgoing'):
            return None
        
        try:
            chat_type = "group" if chat_id < 0 else "user"
            
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'direction': 'outgoing',
                'chat_id': chat_id,
                'chat_type': chat_type,
                'action': action,
                'parse_mode': parse_mode,
                'original_text': text,
                'formatted_text': kwargs.get('formatted_text', text),
                'content_type': kwargs.get('content_type', 'FORMATTED'),
                'success': None,
                'context': context or {}
            }
            
            # Добавляем любые дополнительные параметры
            for key, value in kwargs.items():
                if key not in metadata:
                    metadata[key] = value
            
            log_path = cls.get_log_path('outgoing', chat_id)
            
            # Сохраняем лог
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📤 Outgoing message logged: {log_path}")
            return log_path
            
        except Exception as e:
            logger.error(f"❌ Failed to log outgoing message: {e}")
            return None
    
    @classmethod
    def log_message_to_path(cls, log_path: Path, metadata: Dict[str, Any]) -> Path:
        """
        Сохраняет метаданные в указанный файл (для обратной совместимости)
        """
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return log_path
        except Exception as e:
            logger.error(f"❌ Failed to log message to {log_path}: {e}")
            raise
    
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
