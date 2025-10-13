"""
Модуль для логирования всех этапов работы с LLM
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class LLMLogger:
    """Класс для логирования всех этапов работы с LLM в текстовые файлы"""
    
    def __init__(self, logs_dir: str = "llm_logs", date: Optional[str] = None):
        """
        Инициализация логгера
        
        Args:
            logs_dir: Папка для логов (по умолчанию "llm_logs")
            date: Дата в формате YYYY-MM-DD (по умолчанию текущая дата)
        """
        self.logs_dir = Path(logs_dir)
        
        # Определяем дату
        if date:
            self.date = date
        else:
            self.date = datetime.now().strftime("%Y-%m-%d")
        
        # Создаем папку для текущей даты
        self.date_dir = self.logs_dir / self.date
        self.date_dir.mkdir(parents=True, exist_ok=True)
        
        # Метаданные сессии
        self.session_start = datetime.now()
        self.provider_name = None
        self.model_name = None
        self.chat_id = None
        self.user_id = None
        
        logger.info(f"📁 LLM Logger инициализирован: {self.date_dir}")
    
    def set_session_info(self, provider_name: str, model_name: Optional[str] = None, 
                        chat_id: Optional[str] = None, user_id: Optional[int] = None):
        """
        Установить информацию о сессии
        
        Args:
            provider_name: Название провайдера
            model_name: Название модели
            chat_id: ID чата
            user_id: ID пользователя
        """
        self.provider_name = provider_name
        self.model_name = model_name
        self.chat_id = chat_id
        self.user_id = user_id
        logger.debug(f"📝 Сессия: {provider_name}/{model_name}, чат: {chat_id}, пользователь: {user_id}")
    
    def _write_file(self, filename: str, content: str, step_title: str, 
                   additional_info: Optional[Dict[str, Any]] = None):
        """
        Записать содержимое в файл
        
        Args:
            filename: Имя файла
            content: Содержимое для записи
            step_title: Заголовок этапа
            additional_info: Дополнительная информация
        """
        try:
            file_path = self.date_dir / filename
            
            # Формируем заголовок
            header_lines = [
                f"=== {step_title} ===",
                f"Дата: {self.date}",
                f"Время: {datetime.now().strftime('%H:%M:%S')}",
                f"Провайдер: {self.provider_name or 'неизвестно'}",
            ]
            
            if self.model_name:
                header_lines.append(f"Модель: {self.model_name}")
            if self.chat_id:
                header_lines.append(f"Чат ID: {self.chat_id}")
            if self.user_id:
                header_lines.append(f"Пользователь ID: {self.user_id}")
            
            # Добавляем дополнительную информацию
            if additional_info:
                for key, value in additional_info.items():
                    header_lines.append(f"{key}: {value}")
            
            header_lines.extend(["", content])
            
            # Записываем в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(header_lines))
            
            logger.debug(f"📄 Записан файл: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи файла {filename}: {e}")
    
    def log_formatted_messages(self, formatted_text: str, message_count: int = 0):
        """
        Логировать форматированные сообщения
        
        Args:
            formatted_text: Отформатированный текст сообщений
            message_count: Количество сообщений
        """
        additional_info = {"Количество сообщений": message_count} if message_count > 0 else None
        self._write_file(
            "01_formatted_messages.txt",
            formatted_text,
            "Форматированные сообщения для суммаризации",
            additional_info
        )
    
    def log_llm_request(self, prompt: str, request_type: str = "summarization"):
        """
        Логировать запрос к LLM
        
        Args:
            prompt: Промпт для LLM
            request_type: Тип запроса (summarization, reflection, improvement)
        """
        filename_map = {
            "summarization": "02_summarization_request.txt",
            "reflection": "04_reflection_request.txt", 
            "improvement": "06_improvement_request.txt"
        }
        
        title_map = {
            "summarization": "Запрос суммаризации в LLM",
            "reflection": "Запрос рефлексии в LLM",
            "improvement": "Запрос улучшения в LLM"
        }
        
        filename = filename_map.get(request_type, "02_llm_request.txt")
        title = title_map.get(request_type, "Запрос в LLM")
        
        additional_info = {
            "Тип запроса": request_type,
            "Длина промпта": f"{len(prompt)} символов"
        }
        
        self._write_file(filename, prompt, title, additional_info)
    
    def log_llm_response(self, response: str, request_type: str = "summarization"):
        """
        Логировать ответ от LLM
        
        Args:
            response: Ответ от LLM
            request_type: Тип запроса (summarization, reflection, improvement)
        """
        filename_map = {
            "summarization": "03_summarization_response.txt",
            "reflection": "05_reflection_response.txt",
            "improvement": "07_improvement_response.txt"
        }
        
        title_map = {
            "summarization": "Ответ LLM с суммаризацией",
            "reflection": "Ответ LLM с рефлексией",
            "improvement": "Ответ LLM с улучшением"
        }
        
        filename = filename_map.get(request_type, "03_llm_response.txt")
        title = title_map.get(request_type, "Ответ от LLM")
        
        additional_info = {
            "Тип ответа": request_type,
            "Длина ответа": f"{len(response)} символов"
        }
        
        self._write_file(filename, response, title, additional_info)
    
    def log_raw_result(self, raw_text: str):
        """
        Логировать сырой результат
        
        Args:
            raw_text: Сырой текст результата
        """
        additional_info = {"Длина текста": f"{len(raw_text)} символов"}
        self._write_file(
            "08_raw_result.txt",
            raw_text,
            "Сырой результат суммаризации",
            additional_info
        )
    
    def log_formatted_result(self, formatted_text: str):
        """
        Логировать форматированный результат
        
        Args:
            formatted_text: Форматированный текст для Telegram
        """
        additional_info = {"Длина текста": f"{len(formatted_text)} символов"}
        self._write_file(
            "09_formatted_result.txt",
            formatted_text,
            "Форматированный результат для Telegram",
            additional_info
        )
    
    def log_session_summary(self, summary_data: Dict[str, Any]):
        """
        Логировать сводку сессии
        
        Args:
            summary_data: Данные о сессии
        """
        session_duration = datetime.now() - self.session_start
        
        summary_content = f"""Длительность сессии: {session_duration}
Провайдер: {self.provider_name}
Модель: {self.model_name or 'не указана'}
Чат ID: {self.chat_id or 'не указан'}
Пользователь ID: {self.user_id or 'не указан'}

Результаты:
- Суммаризация: {'✅' if summary_data.get('summary') else '❌'}
- Рефлексия: {'✅' if summary_data.get('reflection') else '❌'}
- Улучшение: {'✅' if summary_data.get('improved') else '❌'}

Файлы созданы:
"""
        
        # Проверяем какие файлы были созданы
        for i in range(1, 10):
            filename = f"{i:02d}_*.txt"
            files = list(self.date_dir.glob(filename))
            if files:
                summary_content += f"- {files[0].name}\n"
        
        self._write_file(
            "00_session_summary.txt",
            summary_content,
            "Сводка сессии логирования",
            {"Длительность": str(session_duration)}
        )
    
    def get_logs_path(self) -> str:
        """
        Получить путь к папке с логами
        
        Returns:
            Путь к папке с логами
        """
        return str(self.date_dir)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Очистить старые логи (старше указанного количества дней)
        
        Args:
            days_to_keep: Количество дней для хранения логов
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for date_dir in self.logs_dir.iterdir():
                if date_dir.is_dir():
                    try:
                        dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                        if dir_date < cutoff_date:
                            import shutil
                            shutil.rmtree(date_dir)
                            logger.info(f"🗑️ Удалена старая папка логов: {date_dir}")
                    except ValueError:
                        # Пропускаем папки с неправильным форматом имени
                        continue
                        
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых логов: {e}")
