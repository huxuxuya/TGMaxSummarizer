"""
Модуль для логирования всех этапов работы с LLM
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def _sanitize_path_component(name: str) -> str:
    """Sanitize string for use in file path"""
    if not name:
        return "unknown"
    # Replace invalid characters
    sanitized = name.replace(":", "_").replace("/", "_").replace("\\", "_")
    sanitized = sanitized.replace("<", "_").replace(">", "_").replace("|", "_")
    sanitized = sanitized.replace("*", "_").replace("?", "_").replace('"', "_")
    return sanitized

class LLMLogger:
    """Класс для логирования всех этапов работы с LLM в текстовые файлы"""
    
    def __init__(self, logs_dir: str = "llm_logs", date: Optional[str] = None, scenario: Optional[str] = None, 
                 test_mode: bool = False, model_name: Optional[str] = None):
        """
        Инициализация логгера
        
        Args:
            logs_dir: Папка для логов (по умолчанию "llm_logs")
            date: Дата в формате YYYY-MM-DD (по умолчанию текущая дата)
            scenario: Сценарий (with_reflection, without_reflection, with_cleaning)
            test_mode: Если True, использует структуру test_comparison/{model_name}/{scenario}/
            model_name: Имя модели для тестового режима
        """
        self.logs_dir = Path(logs_dir)
        
        # Определяем дату
        if date:
            self.date = date
        else:
            self.date = datetime.now().strftime("%Y-%m-%d")
        
        # Создаем подпапку для сценария
        if test_mode and model_name and scenario:
            # Sanitize model name for valid path
            safe_model_name = _sanitize_path_component(model_name)
            # Тестовый режим: test_comparison/{model_name}/{scenario}/
            self.scenario_dir = self.logs_dir / "test_comparison" / safe_model_name / scenario
            # Очищаем папку если существует
            if self.scenario_dir.exists():
                import shutil
                shutil.rmtree(self.scenario_dir)
            self.scenario_dir.mkdir(parents=True, exist_ok=True)
            # Verify directory was created
            if not self.scenario_dir.exists() or not self.scenario_dir.is_dir():
                raise RuntimeError(f"Failed to create log directory: {self.scenario_dir}")
        elif scenario:
            # Обычный режим с временной меткой (папка будет создана позже с учетом модели)
            self.scenario = scenario
            self.scenario_dir = None  # Будет создана в create_scenario_dir
        else:
            # Обычный режим без сценария
            self.scenario_dir = self.logs_dir / self.date
            self.scenario_dir.mkdir(parents=True, exist_ok=True)
            # Verify directory was created
            if not self.scenario_dir.exists() or not self.scenario_dir.is_dir():
                raise RuntimeError(f"Failed to create log directory: {self.scenario_dir}")
        
        # Сохраняем для обратной совместимости
        # date_dir будет установлен в _create_scenario_dir когда папка будет создана
        if self.scenario_dir is not None:
            self.date_dir = self.scenario_dir
        else:
            self.date_dir = None
        
        # Метаданные сессии
        self.session_start = datetime.now()
        self.provider_name = None
        # Save original model name for reference
        self.original_model_name = model_name if (test_mode and model_name) else None
        self.model_name = self.original_model_name  # Save original name
        self.chat_id = None
        self.user_id = None
        
        # Статистика времени выполнения этапов
        self.stage_times = {
            'cleaning': None,
            'summarization': None,
            'reflection': None,
            'improvement': None,
            'classification': None,
            'extraction': None,
            'parent_summary': None
        }
        
        logger.info(f"📁 LLM Logger инициализирован: {self.scenario_dir}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Оценить количество токенов в тексте
        
        Args:
            text: Текст для анализа
            
        Returns:
            Примерное количество токенов
        """
        if not text:
            return 0
        
        # Примерная оценка: 4 символа = 1 токен для большинства языков
        # Для русского текста может быть 3-4 символа на токен
        return len(text) // 4
    
    def _get_token_stats(self, input_text: str, output_text: str = None) -> dict:
        """
        Получить статистику по токенам
        
        Args:
            input_text: Входящий текст
            output_text: Исходящий текст (опционально)
            
        Returns:
            Словарь со статистикой токенов
        """
        input_tokens = self._estimate_tokens(input_text)
        output_tokens = self._estimate_tokens(output_text) if output_text else 0
        total_tokens = input_tokens + output_tokens
        
        stats = {
            "Входящие токены": input_tokens,
            "Исходящие токены": output_tokens,
            "Всего токенов": total_tokens,
            "Длина контекста": len(input_text)
        }
        
        if output_text:
            stats["Длина ответа"] = len(output_text)
        
        return stats
    
    def log_stage_time(self, stage: str, duration: float):
        """
        Записать время выполнения этапа
        
        Args:
            stage: Название этапа (cleaning, summarization, reflection, improvement)
            duration: Время выполнения в секундах
        """
        if stage in self.stage_times:
            self.stage_times[stage] = duration
    
    def clear_date_logs(self):
        """Remove all existing log files for this scenario before starting new session"""
        import shutil
        
        if self.scenario_dir.exists():
            logger.info(f"🗑️  Clearing old logs for scenario: {self.scenario_dir}")
            shutil.rmtree(self.scenario_dir)
            self.scenario_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Old logs cleared, fresh directory created")
    
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
        
        # Создаем папку сценария с учетом имени модели
        self._create_scenario_dir()
        
        logger.debug(f"📝 Сессия: {provider_name}/{model_name}, чат: {chat_id}, пользователь: {user_id}")
    
    def _create_scenario_dir(self):
        """Создать папку сценария с учетом имени модели"""
        if hasattr(self, 'scenario') and self.scenario and self.scenario_dir is None:
            # Используем полную временную метку для хронологической сортировки
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # Формируем имя папки с учетом модели
            if self.model_name:
                # Очищаем имя модели от недопустимых символов для имени папки
                safe_model_name = _sanitize_path_component(self.model_name)
                folder_name = f"{self.scenario}_{safe_model_name}_{timestamp}"
            else:
                folder_name = f"{self.scenario}_{timestamp}"
            
            self.scenario_dir = self.logs_dir / self.date / folder_name
            self.scenario_dir.mkdir(parents=True, exist_ok=True)
            # Устанавливаем date_dir для обратной совместимости
            self.date_dir = self.scenario_dir
            logger.debug(f"📁 Создана папка логов: {self.scenario_dir}")
    
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
            # Убеждаемся, что папка создана
            if self.scenario_dir is None:
                self._create_scenario_dir()
            
            file_path = self.scenario_dir / filename
            
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
            # Re-raise if directory doesn't exist - critical error
            if not self.scenario_dir or not self.scenario_dir.exists():
                raise RuntimeError(f"Log directory does not exist: {self.scenario_dir}") from e
    
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
        
        # Разделяем системный промпт и пользовательские сообщения
        lines = prompt.split('\n')
        formatted_prompt = "=== ПОЛНЫЙ ПРОМПТ ===\n\n"
        formatted_prompt += prompt
        
        # Получаем статистику токенов
        token_stats = self._get_token_stats(prompt)
        
        additional_info = {
            "Тип запроса": request_type,
            "Длина промпта": f"{len(prompt)} символов",
            "Строк": len(lines),
            **token_stats
        }
        
        self._write_file(filename, formatted_prompt, title, additional_info)
    
    def log_llm_response(self, response: str, request_type: str = "summarization", response_time: float = None):
        """
        Логировать ответ от LLM
        
        Args:
            response: Ответ от LLM
            request_type: Тип запроса (summarization, reflection, improvement)
            response_time: Время ответа в секундах
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
        
        # Получаем статистику токенов для ответа
        token_stats = self._get_token_stats("", response)  # Только исходящие токены
        
        additional_info = {
            "Тип ответа": request_type,
            "Длина ответа": f"{len(response)} символов",
            **token_stats
        }
        
        # Добавляем информацию о времени ответа и скорости
        if response_time is not None:
            additional_info["Время ответа"] = f"{response_time:.2f} секунд"
            if response_time > 0:
                tokens_per_sec = token_stats['Исходящие токены'] / response_time
                additional_info["Скорость генерации"] = f"{tokens_per_sec:.1f} токенов/сек"
        
        self._write_file(filename, response, title, additional_info)
    
    def log_token_usage(self, input_text: str, output_text: str, request_type: str = "summarization", response_time: float = None):
        """
        Логировать полную статистику использования токенов
        
        Args:
            input_text: Входящий текст (промпт)
            output_text: Исходящий текст (ответ)
            request_type: Тип запроса
            response_time: Время ответа в секундах
        """
        # Получаем полную статистику токенов
        token_stats = self._get_token_stats(input_text, output_text)
        
        # Формируем содержимое файла
        content = f"=== СТАТИСТИКА ТОКЕНОВ ===\n\n"
        content += f"Тип запроса: {request_type}\n"
        content += f"Время: {datetime.now().strftime('%H:%M:%S')}\n"
        content += f"Провайдер: {self.provider_name}\n"
        content += f"Модель: {self.model_name}\n\n"
        
        content += f"📊 СТАТИСТИКА ТОКЕНОВ:\n"
        content += f"   • Входящие токены: {token_stats['Входящие токены']}\n"
        content += f"   • Исходящие токены: {token_stats['Исходящие токены']}\n"
        content += f"   • Всего токенов: {token_stats['Всего токенов']}\n"
        content += f"   • Длина контекста: {token_stats['Длина контекста']} символов\n"
        content += f"   • Длина ответа: {token_stats['Длина ответа']} символов\n\n"
        
        if response_time is not None:
            content += f"⏱️ ПРОИЗВОДИТЕЛЬНОСТЬ:\n"
            content += f"   • Время ответа: {response_time:.2f} секунд\n"
            if response_time > 0:
                tokens_per_second = token_stats['Исходящие токены'] / response_time
                content += f"   • Скорость генерации: {tokens_per_second:.2f} токенов/сек\n"
        
        # Оценка стоимости (примерная для разных провайдеров)
        content += f"\n💰 ОЦЕНКА СТОИМОСТИ:\n"
        if self.provider_name and "gpt" in self.provider_name.lower():
            # GPT-4: ~$0.03 за 1K токенов входящих, ~$0.06 за 1K исходящих
            input_cost = (token_stats['Входящие токены'] / 1000) * 0.03
            output_cost = (token_stats['Исходящие токены'] / 1000) * 0.06
            total_cost = input_cost + output_cost
            content += f"   • Входящие: ~${input_cost:.4f}\n"
            content += f"   • Исходящие: ~${output_cost:.4f}\n"
            content += f"   • Всего: ~${total_cost:.4f}\n"
        elif self.provider_name and "gemini" in self.provider_name.lower():
            # Gemini Pro: ~$0.0005 за 1K токенов
            total_cost = (token_stats['Всего токенов'] / 1000) * 0.0005
            content += f"   • Всего: ~${total_cost:.4f}\n"
        else:
            content += f"   • Локальная модель (бесплатно)\n"
        
        additional_info = {
            "Тип запроса": request_type,
            **token_stats
        }
        
        if response_time is not None:
            additional_info["Время ответа"] = f"{response_time:.2f}с"
            if response_time > 0:
                additional_info["Скорость генерации"] = f"{token_stats['Исходящие токены'] / response_time:.2f} токенов/сек"
        
        self._write_file("22_token_usage.txt", content, "Статистика использования токенов", additional_info)
    
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
        
        # Форматируем время выполнения этапов
        def format_stage_time(stage_name: str, time_seconds: float) -> str:
            if time_seconds is None:
                return "❌ Не выполнялся"
            return f"✅ {time_seconds:.1f}с"
        
        summary_content = f"""=== Сводка сессии логирования ===
Дата: {self.session_start.strftime('%Y-%m-%d')}
Время: {self.session_start.strftime('%H:%M:%S')}
Провайдер: {self.provider_name}
Модель: {self.model_name or 'не указана'}
Длительность: {session_duration}

Длительность сессии: {session_duration}
Провайдер: {self.provider_name}
Модель: {self.model_name or 'не указана'}
Чат ID: {self.chat_id or 'не указан'}
Пользователь ID: {self.user_id or 'не указан'}

⏱️ Время выполнения этапов:
- Очистка данных: {format_stage_time('Очистка', self.stage_times.get('cleaning'))}
- Суммаризация: {format_stage_time('Суммаризация', self.stage_times.get('summarization'))}
- Рефлексия: {format_stage_time('Рефлексия', self.stage_times.get('reflection'))}
- Улучшение: {format_stage_time('Улучшение', self.stage_times.get('improvement'))}
- Классификация: {format_stage_time('Классификация', self.stage_times.get('classification'))}
- Экстракция: {format_stage_time('Экстракция', self.stage_times.get('extraction'))}
- Сводка для родителей: {format_stage_time('Сводка', self.stage_times.get('parent_summary'))}

Результаты:
- Суммаризация: {'✅' if summary_data.get('summary') else '❌'}
- Рефлексия: {'✅' if summary_data.get('reflection') else '❌'}
- Улучшение: {'✅' if summary_data.get('improved') else '❌'}

Статистика токенов:
- Входящие токены: {summary_data.get('input_tokens', 0)}
- Исходящие токены: {summary_data.get('output_tokens', 0)}
- Всего токенов: {summary_data.get('total_tokens', 0)}

Файлы созданы:
"""
        
        # Проверяем какие файлы были созданы
        for i in range(1, 15):
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
        return str(self.scenario_dir)
    
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
    
    def log_cleaning_request(self, request_text: str):
        """
        Логирует запрос на очистку данных
        
        Args:
            request_text: Текст запроса на очистку
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.date_dir / "10_cleaning_request.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Запрос на очистку данных ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n\n")
                f.write(f"Запрос:\n{request_text}\n")
            
            logger.debug(f"📝 Запрос на очистку данных записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи запроса на очистку: {e}")
    
    def log_cleaning_response(self, response_text: str, response_time: float = None):
        """
        Логирует ответ на запрос очистки данных
        
        Args:
            response_text: Текст ответа с очисткой
            response_time: Время ответа в секундах
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.date_dir / "11_cleaning_response.txt"
            
            # Подсчитываем примерное количество токенов
            estimated_tokens = len(response_text) // 4
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Ответ на запрос очистки данных ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина ответа: {len(response_text)} символов\n")
                f.write(f"Примерное количество токенов: ~{estimated_tokens}\n")
                
                # Добавляем информацию о времени ответа и скорости
                if response_time is not None:
                    f.write(f"Время ответа: {response_time:.2f} секунд\n")
                    if response_time > 0:
                        tokens_per_sec = estimated_tokens / response_time
                        f.write(f"Скорость генерации: {tokens_per_sec:.1f} токенов/сек\n")
                
                f.write(f"\nОтвет:\n{response_text}\n")
            
            logger.debug(f"📝 Ответ на очистку данных записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи ответа на очистку: {e}")
    
    def log_input_messages_raw(self, messages: list):
        """
        Логирует сырые входящие сообщения
        
        Args:
            messages: Список сообщений для логирования
        """
        try:
            import json
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "01_input_messages_raw.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Сырые входящие сообщения ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Количество сообщений: {len(messages)}\n\n")
                f.write(f"JSON данные:\n{json.dumps(messages, ensure_ascii=False, indent=2)}\n")
            
            logger.debug(f"📝 Сырые входящие сообщения записаны: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи сырых входящих сообщений: {e}")
    
    def log_filtered_messages_raw(self, messages: list):
        """
        Логирует отфильтрованные сообщения после очистки
        
        Args:
            messages: Список отфильтрованных сообщений
        """
        try:
            import json
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "02_filtered_messages_raw.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Отфильтрованные сообщения после очистки ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Количество отфильтрованных сообщений: {len(messages)}\n\n")
                f.write(f"JSON данные:\n{json.dumps(messages, ensure_ascii=False, indent=2)}\n")
            
            logger.debug(f"📝 Отфильтрованные сообщения записаны: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи отфильтрованных сообщений: {e}")
    
    def log_improvement_request(self, request_text: str):
        """
        Логирует запрос на улучшение суммаризации
        
        Args:
            request_text: Текст запроса на улучшение
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "12_improvement_request.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Запрос на улучшение суммаризации ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n\n")
                f.write(f"Запрос:\n{request_text}\n")
            
            logger.debug(f"📝 Запрос на улучшение записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи запроса на улучшение: {e}")
    
    def log_improvement_response(self, response_text: str, response_time: float = None):
        """
        Логирует ответ на запрос улучшения суммаризации
        
        Args:
            response_text: Текст ответа с улучшенной суммаризацией
            response_time: Время ответа в секундах
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "13_improvement_response.txt"
            
            # Подсчитываем примерное количество токенов
            estimated_tokens = len(response_text) // 4
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Ответ на запрос улучшения суммаризации ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина ответа: {len(response_text)} символов\n")
                f.write(f"Примерное количество токенов: ~{estimated_tokens}\n")
                
                # Добавляем информацию о времени ответа и скорости
                if response_time is not None:
                    f.write(f"Время ответа: {response_time:.2f} секунд\n")
                    if response_time > 0:
                        tokens_per_sec = estimated_tokens / response_time
                        f.write(f"Скорость генерации: {tokens_per_sec:.1f} токенов/сек\n")
                
                f.write(f"\nОтвет:\n{response_text}\n")
            
            logger.debug(f"📝 Ответ на улучшение записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи ответа на улучшение: {e}")
    
    def log_final_result_raw(self, result):
        """
        Логирует сырой финальный результат
        
        Args:
            result: Финальный результат (может быть строкой или словарем)
        """
        try:
            import json
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "14_final_result_raw.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Сырой финальный результат ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Тип результата: {type(result).__name__}\n\n")
                
                if isinstance(result, dict):
                    f.write(f"JSON данные:\n{json.dumps(result, ensure_ascii=False, indent=2)}\n")
                else:
                    f.write(f"Текст:\n{str(result)}\n")
            
            logger.debug(f"📝 Сырой финальный результат записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи сырого финального результата: {e}")
    
    def log_telegram_formatted(self, formatted_text: str):
        """
        Логирует отформатированный текст для Telegram
        
        Args:
            formatted_text: Текст, отформатированный для отправки в Telegram
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "15_telegram_formatted.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Отформатированный текст для Telegram ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина текста: {len(formatted_text)} символов\n\n")
                f.write(f"Текст:\n{formatted_text}\n")
            
            logger.debug(f"📝 Отформатированный текст для Telegram записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи отформатированного текста: {e}")
    
    # Методы логирования для структурированного анализа
    
    def log_classification_request(self, request_text: str):
        """
        Логирует запрос на классификацию сообщений
        
        Args:
            request_text: Текст запроса на классификацию
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "16_classification_request.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Запрос на классификацию сообщений ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n\n")
                f.write(f"Запрос:\n{request_text}\n")
            
            logger.debug(f"📝 Запрос на классификацию записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи запроса на классификацию: {e}")
    
    def log_classification_response(self, response_text: str, response_time: float = None):
        """
        Логирует ответ на запрос классификации
        
        Args:
            response_text: Текст ответа с классификацией
            response_time: Время ответа в секундах
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "17_classification_response.txt"
            
            # Подсчитываем примерное количество токенов
            estimated_tokens = len(response_text) // 4
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Ответ на запрос классификации ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина ответа: {len(response_text)} символов\n")
                f.write(f"Примерное количество токенов: ~{estimated_tokens}\n")
                
                if response_time is not None:
                    f.write(f"Время ответа: {response_time:.2f} секунд\n")
                    if response_time > 0:
                        tokens_per_sec = estimated_tokens / response_time
                        f.write(f"Скорость генерации: {tokens_per_sec:.1f} токенов/сек\n")
                
                f.write(f"\nОтвет:\n{response_text}\n")
            
            logger.debug(f"📝 Ответ на классификацию записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи ответа на классификацию: {e}")
    
    def log_extraction_request(self, request_text: str):
        """
        Логирует запрос на экстракцию слотов
        
        Args:
            request_text: Текст запроса на экстракцию
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "18_extraction_request.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Запрос на экстракцию слотов ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n\n")
                f.write(f"Запрос:\n{request_text}\n")
            
            logger.debug(f"📝 Запрос на экстракцию записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи запроса на экстракцию: {e}")
    
    def log_extraction_response(self, response_text: str, response_time: float = None):
        """
        Логирует ответ на запрос экстракции
        
        Args:
            response_text: Текст ответа с экстракцией
            response_time: Время ответа в секундах
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "19_extraction_response.txt"
            
            # Подсчитываем примерное количество токенов
            estimated_tokens = len(response_text) // 4
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Ответ на запрос экстракции ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина ответа: {len(response_text)} символов\n")
                f.write(f"Примерное количество токенов: ~{estimated_tokens}\n")
                
                if response_time is not None:
                    f.write(f"Время ответа: {response_time:.2f} секунд\n")
                    if response_time > 0:
                        tokens_per_sec = estimated_tokens / response_time
                        f.write(f"Скорость генерации: {tokens_per_sec:.1f} токенов/сек\n")
                
                f.write(f"\nОтвет:\n{response_text}\n")
            
            logger.debug(f"📝 Ответ на экстракцию записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи ответа на экстракцию: {e}")
    
    def log_parent_summary_request(self, request_text: str):
        """
        Логирует запрос на генерацию сводки для родителей
        
        Args:
            request_text: Текст запроса на сводку
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "20_parent_summary_request.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Запрос на генерацию сводки для родителей ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n\n")
                f.write(f"Запрос:\n{request_text}\n")
            
            logger.debug(f"📝 Запрос на сводку для родителей записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи запроса на сводку для родителей: {e}")
    
    def log_parent_summary_response(self, response_text: str, response_time: float = None):
        """
        Логирует ответ на запрос сводки для родителей
        
        Args:
            response_text: Текст ответа со сводкой
            response_time: Время ответа в секундах
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_file = self.scenario_dir / "21_parent_summary_response.txt"
            
            # Подсчитываем примерное количество токенов
            estimated_tokens = len(response_text) // 4
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Ответ на запрос сводки для родителей ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Длина ответа: {len(response_text)} символов\n")
                f.write(f"Примерное количество токенов: ~{estimated_tokens}\n")
                
                if response_time is not None:
                    f.write(f"Время ответа: {response_time:.2f} секунд\n")
                    if response_time > 0:
                        tokens_per_sec = estimated_tokens / response_time
                        f.write(f"Скорость генерации: {tokens_per_sec:.1f} токенов/сек\n")
                
                f.write(f"\nОтвет:\n{response_text}\n")
            
            logger.debug(f"📝 Ответ на сводку для родителей записан: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи ответа на сводку для родителей: {e}")
    
    def log_error(self, stage: str, error_message: str, exception_details: str = None):
        """
        Логирует ошибку на определённом этапе
        
        Args:
            stage: Название этапа (classification, extraction, parent_summary и т.д.)
            error_message: Сообщение об ошибке
            exception_details: Детали исключения
        """
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Определяем имя файла в зависимости от этапа
            stage_file_map = {
                'classification': '22_classification_error.txt',
                'extraction': '23_extraction_error.txt',
                'parent_summary': '24_parent_summary_error.txt',
                'summarization': '25_summarization_error.txt',
                'reflection': '26_reflection_error.txt',
                'improvement': '27_improvement_error.txt'
            }
            
            filename = stage_file_map.get(stage, '28_error.txt')
            log_file = self.scenario_dir / filename
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== ОШИБКА: {stage.upper()} ===\n")
                f.write(f"Время: {timestamp}\n")
                f.write(f"Провайдер: {self.provider_name}\n")
                f.write(f"Модель: {self.model_name}\n")
                f.write(f"Пользователь: {self.user_id}\n")
                f.write(f"Чат: {self.chat_id}\n")
                f.write(f"Этап: {stage}\n\n")
                f.write(f"Сообщение об ошибке:\n{error_message}\n")
                
                if exception_details:
                    f.write(f"\nДетали исключения:\n{exception_details}\n")
            
            logger.debug(f"📝 Ошибка записана: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка записи лога ошибки: {e}")