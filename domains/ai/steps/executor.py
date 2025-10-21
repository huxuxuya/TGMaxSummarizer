"""
Упрощенный исполнитель шагов для композиционного анализа
"""
import time
import logging
from typing import List, Any, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..models import StepType, AnalysisResult, AnalysisType
from ..service import PipelineContext
from infrastructure.logging.log_session import LogSession

class StepExecutor:
    """Исполнитель шагов для композиционного анализа с централизованным логированием"""
    
    # Маппинг типов шагов на типы логов
    STEP_TO_LOG_TYPE = {
        StepType.CLEANING: "cleaning",
        StepType.SUMMARIZATION: "summarization",
        StepType.REFLECTION: "reflection",
        StepType.IMPROVEMENT: "improvement",
        StepType.CLASSIFICATION: "classification",
        StepType.EXTRACTION: "extraction",
        StepType.SCHEDULE_ANALYSIS: "schedule_analysis",
        StepType.PARENT_SUMMARY: "parent_summary"
    }
    
    def __init__(self, context: PipelineContext):
        self.context = context
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем LogSession если не установлен
        if not self.context.log_session and self.context.request.llm_logger:
            self._init_log_session()
    
    def _init_log_session(self):
        """Инициализировать LogSession для централизованного логирования"""
        if not self.context.request.llm_logger:
            return
        
        # Получаем базовый путь из llm_logger
        logs_path = self.context.request.llm_logger.get_logs_path()
        if not logs_path or logs_path == 'None' or logs_path == 'None':
            # Если папка еще не создана, создаем временную
            from datetime import datetime
            temp_dir = Path("temp_logs") / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            base_path = temp_dir
            self.logger.warning(f"⚠️ LLM logger папка не создана, используем временную: {base_path}")
        else:
            base_path = Path(logs_path)
        
        # Метаданные запуска
        run_meta = {
            "scenario": getattr(self.context.request, 'scenario', 'unknown'),
            "provider": self.context.request.provider_name,
            "model": self.context.request.model_id,
            "chat_id": getattr(self.context.request, 'chat_id', None),
            "user_id": getattr(self.context.request, 'user_id', None),
            "analysis_type": self.context.request.analysis_type.value if self.context.request.analysis_type else 'unknown'
        }
        
        self.context.log_session = LogSession(base_path, run_meta)
        self.logger.info(f"📋 LogSession инициализирован: {base_path}")
    
    def _get_input_for_step(self, preferred_steps: List[str] = None) -> Any:
        """
        Получить входные данные для текущего шага
        
        Args:
            preferred_steps: Список предпочитаемых шагов в порядке приоритета
            
        Returns:
            Результат предыдущего шага или исходные сообщения
        """
        # Если указаны предпочитаемые шаги, ищем их результаты
        if preferred_steps:
            for step in preferred_steps:
                result = self.context.step_results.get(step)
                if result:
                    self.logger.debug(f"📥 Используем результат шага '{step}' как входные данные")
                    return result
        
        # Если ничего не нашли, используем исходные сообщения
        self.logger.debug(f"📥 Используем исходные сообщения как входные данные")
        return self.context.request.messages
    
    async def execute_steps(self, steps: List[StepType]) -> AnalysisResult:
        """Выполнить список шагов последовательно"""
        start_time = time.time()
        
        try:
            for i, step in enumerate(steps):
                self.logger.info(f"📋 Выполнение шага {i+1}/{len(steps)}: {step}")
                try:
                    result = await self._execute_single_step(step)
                    self.context.step_results[step.value] = result
                    self.logger.info(f"✅ Шаг {step} завершен успешно")
                except Exception as step_error:
                    self.logger.error(f"❌ Ошибка в шаге {step}: {step_error}")
                    raise step_error
            
            return self._build_result(steps, time.time() - start_time)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка выполнения шагов: {e}")
            return AnalysisResult(
                success=False, 
                error=str(e),
                provider_name=self.context.request.provider_name,
                model_id=self.context.request.model_id,
                processing_time=time.time() - start_time,
                analysis_type=AnalysisType.SUMMARIZATION
            )
    
    async def _execute_single_step(self, step: StepType) -> Any:
        """Выполнить один шаг с централизованным логированием"""
        
        # Получаем тип лога для текущего шага
        log_type = self.STEP_TO_LOG_TYPE.get(step, "general")
        
        # Маршрутизируем на соответствующий метод с логированием
        if step == StepType.CLEANING:
            return await self._do_cleaning_with_logging(log_type)
        elif step == StepType.SUMMARIZATION:
            return await self._do_summarization_with_logging(log_type)
        elif step == StepType.REFLECTION:
            return await self._do_reflection_with_logging(log_type)
        elif step == StepType.IMPROVEMENT:
            return await self._do_improvement_with_logging(log_type)
        elif step == StepType.CLASSIFICATION:
            return await self._do_classification_with_logging(log_type)
        elif step == StepType.EXTRACTION:
            return await self._do_extraction_with_logging(log_type)
        elif step == StepType.SCHEDULE_ANALYSIS:
            return await self._do_schedule_analysis_with_logging(log_type)
        elif step == StepType.PARENT_SUMMARY:
            return await self._do_parent_summary_with_logging(log_type)
        else:
            raise ValueError(f"Неизвестный шаг: {step}")
    
    async def _do_cleaning(self) -> List[Dict]:
        """Логика из DataCleaningPipeline"""
        self.logger.info("🧹 Выполнение очистки данных")
        
        messages = self.context.request.messages
        
        if not messages:
            raise ValueError("Нет сообщений для очистки")
        
        self.logger.info(f"🧹 Начинаем очистку {len(messages)} сообщений")
        
        cleaning_prompt = self._create_cleaning_prompt(messages)
        response = await self.context.provider.generate_response(cleaning_prompt)
        
        if not response:
            self.logger.warning("Не удалось получить ответ от LLM для очистки, возвращаем исходные сообщения")
            return messages
        
        selected_ids = self._parse_cleaning_response(response)
        
        if not selected_ids:
            self.logger.warning("Не удалось получить список ID для очистки, возвращаем исходные сообщения")
            return messages
        
        cleaned_messages = self._filter_messages_by_ids(messages, selected_ids)
        self.logger.info(f"✅ Очистка завершена: {len(cleaned_messages)} из {len(messages)} сообщений")
        
        return cleaned_messages
    
    def _create_cleaning_prompt(self, messages: list) -> str:
        """Создать промпт для очистки"""
        messages_text = ""
        for i, msg in enumerate(messages):
            message_id = msg.get('id', i)
            text = msg.get('text', '').strip()
            if text:
                messages_text += f"ID: {message_id}\nТекст: {text}\n\n"
        
        return f"""Отфильтруй сообщения чата, оставив только те, которые содержат важную информацию для родителей.

СООБЩЕНИЯ:
{messages_text}

Исключи:
- Координационные сообщения ("кто заберет", "во сколько", "где встречаемся")
- Микроменеджмент ("не забудьте", "напомните детям")
- Несущественную информацию
- Повторяющиеся сообщения
- Короткие реакции ("ок", "спасибо", "понял")

Оставь:
- Важные объявления
- Информацию о мероприятиях
- Правила и требования
- Проблемы и жалобы
- Образовательную информацию

Верни только JSON массив с ID сообщений для сохранения:
[1, 5, 12, 23, ...]"""
    
    def _parse_cleaning_response(self, response: str) -> list:
        """Парсить ответ очистки"""
        import json
        import re
        
        try:
            json_match = re.search(r'\[[\d,\s]+\]', response)
            if not json_match:
                self.logger.error(f"Не удалось найти JSON массив в ответе: {response}")
                return []
            
            selected_ids = json.loads(json_match.group())
            return selected_ids
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON очистки: {e}")
            return []
    
    def _filter_messages_by_ids(self, messages: list, selected_ids: list) -> list:
        """Фильтровать сообщения по выбранным ID"""
        cleaned_messages = []
        for i, msg in enumerate(messages):
            message_id = msg.get('id', i)
            if message_id in selected_ids:
                cleaned_messages.append(msg)
        return cleaned_messages
    
    async def _do_summarization(self) -> str:
        """Логика из SummarizationPipeline"""
        self.logger.info("📝 Выполнение суммаризации")
        
        messages = self.context.step_results.get('cleaning', self.context.request.messages)
        chat_context = self.context.request.chat_context or {}
        
        if not messages:
            raise ValueError("Нет сообщений для анализа")
        
        self.logger.info(f"📝 Начинаем суммаризацию {len(messages)} сообщений")
        
        summary = await self.context.provider.summarize_chat(messages, chat_context)
        
        if not summary:
            raise ValueError("Не удалось получить суммаризацию")
        
        self.logger.info(f"✅ Суммаризация получена ({len(summary)} символов)")
        return summary
    
    async def _do_reflection(self) -> str:
        """Логика из ReflectionPipeline"""
        self.logger.info("🤔 Выполнение рефлексии")
        
        summary = self.context.step_results.get('summarization')
        if not summary:
            raise ValueError("Нет результата суммаризации для рефлексии")
        
        self.logger.info("🤔 Начинаем рефлексию над суммаризацией")
        
        reflection_prompt = self._create_reflection_prompt(summary)
        reflection = await self.context.provider.generate_response(reflection_prompt)
        
        if not reflection:
            raise ValueError("Не удалось получить рефлексию")
        
        self.logger.info(f"✅ Рефлексия получена ({len(reflection)} символов)")
        return reflection
    
    def _create_reflection_prompt(self, summary: str) -> str:
        """Создать промпт для рефлексии"""
        messages = self.context.request.messages
        total_messages = len(messages)
        date = self.context.request.chat_context.get('date', 'неизвестная дата') if self.context.request.chat_context else 'неизвестная дата'
        
        # Форматируем исходные сообщения для анализа
        # Ограничиваем количество для экономии токенов (первые 50 сообщений)
        max_messages = min(50, total_messages)
        formatted_messages = ""
        
        for i, msg in enumerate(messages[:max_messages]):
            message_id = msg.get('id', i + 1)
            text = msg.get('text', '').strip()
            time_str = msg.get('time', '??:??')
            
            # Используем новую функцию с ID и временем, но для Виктории Романовны оставляем как есть
            from shared.utils import get_sender_display_name_with_id
            sender_id = msg.get('sender_id')
            sender = get_sender_display_name_with_id(
                sender_id,
                msg.get('sender', 'Неизвестно'),
                time_str
            )
            
            if text:
                # Компактный формат для экономии токенов
                formatted_messages += f"{i+1}. {sender}: {text}\n"
        
        # Добавляем информацию о пропущенных сообщениях
        if total_messages > max_messages:
            formatted_messages += f"\n... и еще {total_messages - max_messages} сообщений\n"
        
        return f"""Проанализируй следующую суммаризацию чата и дай критическую оценку:

СУММАРИЗАЦИЯ:
{summary}

ИСХОДНЫЕ СООБЩЕНИЯ (первые {max_messages} из {total_messages}):
{formatted_messages}

КОНТЕКСТ:
- Дата: {date}
- Всего сообщений: {total_messages}
- Проанализировано: {max_messages}

Пожалуйста, проанализируй:
1. Полноту охвата информации (сравни с исходными сообщениями)
2. Точность изложения фактов (проверь по исходным данным)
3. Структурированность и логичность
4. Пропущенные важные детали (что не вошло в суммаризацию)
5. Возможные улучшения

Дай конструктивную критику и предложения по улучшению."""
    
    async def _do_improvement(self) -> str:
        """Логика из ReflectionPipeline"""
        self.logger.info("✨ Выполнение улучшения")
        
        # Проверяем доступные результаты шагов
        self.logger.info(f"📊 Доступные результаты шагов: {list(self.context.step_results.keys())}")
        
        original_summary = self.context.step_results.get('summarization')
        reflection = self.context.step_results.get('reflection')
        
        self.logger.info(f"📝 Исходная суммаризация: {'есть' if original_summary else 'НЕТ'}")
        self.logger.info(f"🤔 Рефлексия: {'есть' if reflection else 'НЕТ'}")
        
        if not original_summary:
            raise ValueError("Нет данных исходной суммаризации для улучшения")
        if not reflection:
            raise ValueError("Нет данных рефлексии для улучшения")
        
        self.logger.info("✨ Начинаем улучшение суммаризации")
        
        improvement_prompt = self._create_improvement_prompt(original_summary, reflection)
        self.logger.info(f"📝 Промпт для улучшения создан ({len(improvement_prompt)} символов)")
        
        improved_summary = await self.context.provider.generate_response(improvement_prompt)
        
        if not improved_summary:
            raise ValueError("Не удалось получить улучшенную суммаризацию")
        
        self.logger.info(f"✅ Улучшенная суммаризация получена ({len(improved_summary)} символов)")
        return improved_summary
    
    def _create_improvement_prompt(self, original_summary: str, reflection: str) -> str:
        """Создать промпт для улучшения"""
        return f"""На основе исходной суммаризации и анализа, создай улучшенную версию:

ИСХОДНАЯ СУММАРИЗАЦИЯ:
{original_summary}

АНАЛИЗ И КРИТИКА:
{reflection}

Создай улучшенную суммаризацию, которая:
1. Учитывает замечания из анализа
2. Более структурирована и логична
3. Содержит все важные детали
4. Легко читается и понимается

УЛУЧШЕННАЯ СУММАРИЗАЦИЯ:"""
    
    async def _do_classification(self) -> List[Dict]:
        """Логика из StructuredAnalysisPipeline"""
        self.logger.info("📊 Выполнение классификации")
        
        messages = self.context.request.messages
        
        if not messages:
            raise ValueError("Нет сообщений для классификации")
        
        self.logger.info(f"📊 Начинаем классификацию {len(messages)} сообщений")
        
        classification_prompt = self._create_classification_prompt(messages)
        response = await self.context.provider.generate_response(classification_prompt)
        
        if not response:
            raise ValueError("Не удалось получить классификацию")
        
        classification = self._parse_classification_response(response)
        self.logger.info(f"✅ Классификация получена: {len(classification)} сообщений")
        
        return classification
    
    def _create_classification_prompt(self, input_data: Any) -> str:
        """Создать промпт для классификации"""
        import json
        
        # Если входные данные - это список сообщений
        if isinstance(input_data, list):
            messages_json = json.dumps([
                {"id": msg.get('message_id', msg.get('id', '')), "text": msg.get('text')} 
                for msg in input_data
            ], ensure_ascii=False)
            
            data_section = f"СООБЩЕНИЯ:\n{messages_json}"
        
        # Если это текст (например, суммаризация)
        else:
            data_section = f"ТЕКСТ ДЛЯ КЛАССИФИКАЦИИ:\n{input_data}"
        
        return f"""Классифицируй следующие данные по типам:

{data_section}

Классифицируй каждое сообщение (или фрагмент текста) по следующим категориям:
- "important": Важная информация для родителей
- "coordination": Координация и планирование
- "micromanagement": Микроменеджмент
- "irrelevant": Несущественная информация
- "release_pickup": Информация о заборе детей
- "rules": Правила и требования
- "events": Мероприятия и события
- "problems": Проблемы и жалобы

Верни только JSON массив с объектами:
[{{"message_id": "id", "class": "category"}}, ...]"""
    
    def _create_extraction_prompt(self, input_data: Any) -> str:
        """Создать промпт для экстракции событий"""
        import json
        
        # Если входные данные - это список сообщений
        if isinstance(input_data, list):
            messages_json = json.dumps([
                {"id": msg.get('message_id', msg.get('id', '')), "text": msg.get('text')} 
                for msg in input_data
            ], ensure_ascii=False)
            
            data_section = f"СООБЩЕНИЯ:\n{messages_json}"
        
        # Если это текст (например, суммаризация)
        else:
            data_section = f"ТЕКСТ ДЛЯ ЭКСТРАКЦИИ:\n{input_data}"
        
        return f"""Извлеки важные события и информацию из следующих данных:

{data_section}

Извлеки следующие типы информации:
- "events": Мероприятия и события
- "important": Важная информация для родителей
- "rules": Правила и требования
- "problems": Проблемы и жалобы
- "schedule": Информация о расписании
- "announcements": Объявления

Верни только JSON массив с объектами:
[{{"type": "event_type", "message_id": "id", "description": "описание события"}}, ...]"""
    
    def _parse_classification_response(self, response: str) -> list:
        """Парсить ответ классификации"""
        import json
        import re
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                self.logger.error(f"Не удалось найти JSON массив в ответе: {response}")
                return []
            
            classification = json.loads(json_match.group())
            return classification
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON классификации: {e}")
            return []
    
    def _parse_extraction_response(self, response: str) -> list:
        """Парсить ответ экстракции"""
        import json
        import re
        
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                self.logger.error(f"Не удалось найти JSON массив в ответе: {response}")
                return []
            
            extraction = json.loads(json_match.group())
            return extraction
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга JSON экстракции: {e}")
            return []
    
    async def _do_extraction(self) -> List[Dict]:
        """Логика из StructuredAnalysisPipeline"""
        self.logger.info("🔍 Выполнение экстракции")
        
        classification = self.context.step_results.get('classification')
        if not classification:
            raise ValueError("Нет результатов классификации")
        
        self.logger.info("🔍 Начинаем экстракцию слотов")
        
        # Упрощенная экстракция - возвращаем классификацию как есть
        events = []
        for item in classification:
            if item.get('class') in ['events', 'important', 'rules']:
                events.append({
                    'type': item.get('class'),
                    'message_id': item.get('message_id'),
                    'description': f"Событие типа {item.get('class')}"
                })
        
        self.logger.info(f"✅ Экстракция завершена: {len(events)} событий")
        return events
    
    async def _do_schedule_analysis(self) -> str:
        """НОВОЕ: Анализ расписания на завтра"""
        self.logger.info("📅 Выполнение анализа расписания")
        
        try:
            # Получаем group_id из контекста
            group_id = self.context.request.chat_context.get('group_id')
            if not group_id:
                return "❌ Не удалось определить группу для анализа расписания"
            
            # Для тестирования используем мок-данные
            # В реальном использовании здесь будет запрос к базе данных
            mock_schedule_text = """
            Понедельник: 09:00 Математика, 10:30 Русский язык
            Вторник: 09:00 Английский, 11:00 Физкультура
            Среда: 09:00 История, 10:30 Биология
            Четверг: 09:00 География, 11:00 Химия
            Пятница: 09:00 Литература, 10:30 Физика
            """
            
            # Анализируем расписание на завтра
            tomorrow_schedule = await self._extract_tomorrow_schedule(mock_schedule_text)
            
            if not tomorrow_schedule:
                return "📅 Расписание на завтра не найдено"
            
            return f"📅 **Расписание на завтра:**\n{tomorrow_schedule}"
            
        except Exception as e:
            self.logger.error(f"Ошибка анализа расписания: {e}")
            return f"❌ Ошибка анализа расписания: {str(e)}"
    
    async def _extract_tomorrow_schedule(self, schedule_text: str) -> str:
        """Извлечь расписание на завтра из OCR текста"""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_weekday = tomorrow.strftime("%A").lower()
        
        # Промпт для извлечения расписания на завтра
        prompt = f"""
        Проанализируй текст расписания и найди занятия на {tomorrow.strftime('%d.%m.%Y')} ({tomorrow_weekday}).

        Текст расписания:
        {schedule_text}

        Извлеки:
        1. Время занятий
        2. Названия предметов/активностей
        3. Место проведения (если указано)
        4. Дополнительную информацию

        Если расписание на этот день не найдено, напиши "Расписание на {tomorrow.strftime('%d.%m.%Y')} не найдено".

        Формат ответа:
        **{tomorrow.strftime('%d.%m.%Y')} ({tomorrow_weekday})**
        • Время - Предмет/Активность
        • Время - Предмет/Активность
        ...
        """
        
        response = await self.context.provider.generate_response(prompt)
        return response or "❌ Не удалось проанализировать расписание"
    
    async def _do_parent_summary(self) -> str:
        """Логика из StructuredAnalysisPipeline"""
        self.logger.info("👨‍👩‍👧‍👦 Выполнение сводки для родителей")
        
        events = self.context.step_results.get('extraction')
        if not events:
            raise ValueError("Нет событий для сводки")
        
        self.logger.info("📝 Генерируем сводку для родителей")
        
        summary_prompt = self._create_parent_summary_prompt(events)
        summary = await self.context.provider.generate_response(summary_prompt)
        
        if not summary:
            raise ValueError("Не удалось получить сводку")
        
        self.logger.info(f"✅ Сводка сгенерирована ({len(summary)} символов)")
        return summary
    
    def _create_parent_summary_prompt(self, input_data: Any) -> str:
        """Создать промпт для сводки родителей"""
        import json
        
        # Если входные данные - это список событий/объектов
        if isinstance(input_data, list):
            events_text = ""
            for event in input_data:
                events_text += f"- {event.get('type', 'unknown')}: {event.get('description', '')}\n"
            
            data_section = f"СОБЫТИЯ:\n{events_text}"
        
        # Если это текст (например, суммаризация)
        else:
            data_section = f"ДАННЫЕ ДЛЯ СВОДКИ:\n{input_data}"
        
        return f"""Создай краткую сводку для родителей на основе следующих данных:

{data_section}

Создай структурированную сводку, которая:
1. Кратко описывает основные события дня
2. Выделяет важную информацию для родителей
3. Указывает на действия, которые нужно предпринять
4. Легко читается и понимается

СВОДКА ДЛЯ РОДИТЕЛЕЙ:"""
    
    async def _get_schedule_text_from_db(self) -> Optional[str]:
        """Получить OCR текст расписания из базы данных"""
        try:
            # Получаем group_id из контекста запроса
            group_id = self.context.request.chat_context.get('group_id')
            if not group_id:
                self.logger.warning("Group ID не найден в контексте запроса")
                return None
            
            # Импортируем репозиторий для работы с расписанием
            from domains.chats.repository import ScheduleAnalysisRepository
            from core.database.connection import DatabaseConnection
            
            # Получаем соединение с БД из контекста приложения
            from core.app_context import get_app_context
            ctx = get_app_context()
            
            schedule_repo = ScheduleAnalysisRepository(ctx.db_connection)
            schedule_analysis = schedule_repo.get_schedule_analysis(group_id)
            
            if schedule_analysis and schedule_analysis.get('analysis_text'):
                self.logger.info(f"📅 Найдено расписание для группы {group_id}")
                return schedule_analysis['analysis_text']
            else:
                self.logger.warning(f"📅 Расписание для группы {group_id} не найдено")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка получения расписания из БД: {e}")
            return None
    
    def _create_schedule_analysis_prompt(self, input_data: Any, schedule_text: str) -> str:
        """Создать промпт для анализа расписания"""
        from datetime import datetime, timedelta
        from shared.prompts import FormattingRequirements
        
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_weekday = tomorrow.strftime("%A").lower()
        formatting_rules = FormattingRequirements.get_formatting_instructions("markdown")
        
        # Если входные данные - это список сообщений
        if isinstance(input_data, list):
            messages_text = ""
            for msg in input_data:
                text = msg.get('text', '').strip()
                if text:
                    messages_text += f"{text}\n"
            
            data_section = f"СООБЩЕНИЯ:\n{messages_text}"
        
        # Если это текст (например, суммаризация)
        else:
            data_section = f"СУММАРИЗАЦИЯ:\n{input_data}"
        
        return f"""Проанализируй следующие данные и добавь информацию о расписании на завтра ({tomorrow.strftime('%d.%m.%Y')} - {tomorrow_weekday}).

{data_section}

OCR ТЕКСТ РАСПИСАНИЯ:
{schedule_text}

Задача:
1. Проанализируй OCR текст расписания
2. Найди информацию о занятиях на завтра ({tomorrow.strftime('%d.%m.%Y')})
3. Сопоставь предметы из расписания с домашними заданиями из суммаризации
4. Добавь эту информацию к существующей суммаризации

Если расписание на {tomorrow.strftime('%d.%m.%Y')} не найдено в OCR тексте, напиши "Расписание на {tomorrow.strftime('%d.%m.%Y')} не найдено в расписании".

Формат ответа:
[Существующая суммаризация]

📅 **Расписание на завтра ({tomorrow.strftime('%d.%m.%Y')}):**
• Время - Предмет/Активность
• Время - **Предмет** ⚠️ (ДЗ: описание задания) - если в суммаризации есть ДЗ по этому предмету
• Время - Предмет/Активность
...

ВАЖНО: Если в суммаризации упоминается домашнее задание по какому-либо предмету из расписания на завтра:
- Выдели этот предмет жирным шрифтом (**Предмет**)
- Добавь эмодзи ⚠️ 
- В скобках укажи домашнее задание: (ДЗ: описание)

Примеры:
• 09:00 - **Математика** ⚠️ (ДЗ: стр. 45-47, задачи 12-15)
• 10:30 - Русский язык
• 12:00 - **Физкультура** ⚠️ (ДЗ: принести спортивную форму)

{formatting_rules}"""
    
    # ===== НОВЫЕ МЕТОДЫ С ЦЕНТРАЛИЗОВАННЫМ ЛОГИРОВАНИЕМ =====
    
    async def _do_summarization_with_logging(self, log_type: str) -> str:
        """Суммаризация с централизованным логированием"""
        self.logger.info("📝 Выполнение суммаризации")
        
        messages = self.context.step_results.get('cleaning', self.context.request.messages)
        chat_context = self.context.request.chat_context or {}
        
        if not messages:
            raise ValueError("Нет сообщений для анализа")
        
        self.logger.info(f"📝 Начинаем суммаризацию {len(messages)} сообщений")
        
        # Форматируем и логируем ПЕРЕД вызовом провайдера
        formatted_text = self.context.provider.format_messages_for_analysis(messages)
        if self.context.request.llm_logger:
            self.context.request.llm_logger.log_formatted_messages(formatted_text, len(messages))
        
        # Создаем промпт
        from shared.prompts import PromptTemplates
        prompt = PromptTemplates.get_summarization_prompt(formatted_text, self.context.provider.get_name())
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "summarization", "request", prompt,
                {"message_count": len(messages), "log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        summary = await self.context.provider.generate_response(prompt)  # Напрямую, не через summarize_chat
        response_time = time.time() - start_time
        
        if not summary:
            raise ValueError("Не удалось получить суммаризацию")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "summarization", "response", summary,
                {"response_time": response_time, "log_type": log_type}
            )
        
        self.logger.info(f"✅ Суммаризация получена ({len(summary)} символов)")
        return summary
    
    async def _do_reflection_with_logging(self, log_type: str) -> str:
        """Рефлексия с централизованным логированием"""
        self.logger.info("🤔 Выполнение рефлексии")
        
        summary = self.context.step_results.get('summarization')
        if not summary:
            raise ValueError("Нет результата суммаризации для рефлексии")
        
        self.logger.info("🤔 Начинаем рефлексию над суммаризацией")
        
        # Создаем промпт
        reflection_prompt = self._create_reflection_prompt(summary)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "reflection", "request", reflection_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        reflection = await self.context.provider.generate_response(reflection_prompt)
        response_time = time.time() - start_time
        
        if not reflection:
            raise ValueError("Не удалось получить рефлексию")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "reflection", "response", reflection,
                {"response_time": response_time, "log_type": log_type}
            )
        
        self.logger.info(f"✅ Рефлексия получена ({len(reflection)} символов)")
        return reflection
    
    async def _do_improvement_with_logging(self, log_type: str) -> str:
        """Улучшение с централизованным логированием"""
        self.logger.info("✨ Выполнение улучшения")
        
        # Проверяем доступные результаты шагов
        self.logger.info(f"📊 Доступные результаты шагов: {list(self.context.step_results.keys())}")
        
        original_summary = self.context.step_results.get('summarization')
        reflection = self.context.step_results.get('reflection')
        
        self.logger.info(f"📝 Исходная суммаризация: {'есть' if original_summary else 'НЕТ'}")
        self.logger.info(f"🤔 Рефлексия: {'есть' if reflection else 'НЕТ'}")
        
        if not original_summary:
            raise ValueError("Нет данных исходной суммаризации для улучшения")
        if not reflection:
            raise ValueError("Нет данных рефлексии для улучшения")
        
        self.logger.info("✨ Начинаем улучшение суммаризации")
        
        improvement_prompt = self._create_improvement_prompt(original_summary, reflection)
        self.logger.info(f"📝 Промпт для улучшения создан ({len(improvement_prompt)} символов)")
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "improvement", "request", improvement_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        improved_summary = await self.context.provider.generate_response(improvement_prompt)
        response_time = time.time() - start_time
        
        if not improved_summary:
            raise ValueError("Не удалось получить улучшенную суммаризацию")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "improvement", "response", improved_summary,
                {"response_time": response_time, "log_type": log_type}
            )
        
        self.logger.info(f"✅ Улучшенная суммаризация получена ({len(improved_summary)} символов)")
        return improved_summary
    
    async def _do_cleaning_with_logging(self, log_type: str) -> List[Dict]:
        """Очистка данных с централизованным логированием"""
        self.logger.info("🧹 Выполнение очистки данных")
        
        messages = self.context.request.messages
        
        if not messages:
            raise ValueError("Нет сообщений для очистки")
        
        self.logger.info(f"🧹 Начинаем очистку {len(messages)} сообщений")
        
        cleaning_prompt = self._create_cleaning_prompt(messages)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "cleaning", "request", cleaning_prompt,
                {"message_count": len(messages), "log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        response = await self.context.provider.generate_response(cleaning_prompt)
        response_time = time.time() - start_time
        
        if not response:
            self.logger.warning("Не удалось получить ответ от LLM для очистки, возвращаем исходные сообщения")
            return messages
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "cleaning", "response", response,
                {"response_time": response_time, "log_type": log_type}
            )
        
        selected_ids = self._parse_cleaning_response(response)
        
        if not selected_ids:
            self.logger.warning("Не удалось получить список ID для очистки, возвращаем исходные сообщения")
            return messages
        
        cleaned_messages = self._filter_messages_by_ids(messages, selected_ids)
        self.logger.info(f"✅ Очистка завершена: {len(cleaned_messages)} из {len(messages)} сообщений")
        
        return cleaned_messages
    
    async def _do_classification_with_logging(self, log_type: str) -> List[Dict]:
        """Классификация с централизованным логированием"""
        self.logger.info("🔍 Выполнение классификации")
        
        # Пытаемся получить результат предыдущих шагов или исходные сообщения
        input_data = self._get_input_for_step(['summarization', 'cleaning'])
        
        if not input_data:
            raise ValueError("Нет данных для классификации")
        
        classification_prompt = self._create_classification_prompt(input_data)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "classification", "request", classification_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        response = await self.context.provider.generate_response(classification_prompt)
        response_time = time.time() - start_time
        
        if not response:
            raise ValueError("Не удалось получить классификацию")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "classification", "response", response,
                {"response_time": response_time, "log_type": log_type}
            )
        
        events = self._parse_classification_response(response)
        self.logger.info(f"✅ Классификация завершена: {len(events)} событий")
        
        return events
    
    async def _do_extraction_with_logging(self, log_type: str) -> List[Dict]:
        """Извлечение событий с централизованным логированием"""
        self.logger.info("📋 Выполнение извлечения событий")
        
        # Пытаемся получить результат классификации или работаем с другими данными
        input_data = self._get_input_for_step(['classification', 'summarization', 'cleaning'])
        
        if not input_data:
            raise ValueError("Нет данных для экстракции")
        
        extraction_prompt = self._create_extraction_prompt(input_data)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "extraction", "request", extraction_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        response = await self.context.provider.generate_response(extraction_prompt)
        response_time = time.time() - start_time
        
        if not response:
            raise ValueError("Не удалось получить извлечение событий")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "extraction", "response", response,
                {"response_time": response_time, "log_type": log_type}
            )
        
        extracted_events = self._parse_extraction_response(response)
        self.logger.info(f"✅ Извлечение завершено: {len(extracted_events)} событий")
        
        return extracted_events
    
    async def _do_schedule_analysis_with_logging(self, log_type: str) -> str:
        """Анализ расписания с централизованным логированием"""
        self.logger.info("📅 Выполнение анализа расписания")
        
        # Получаем OCR текст расписания из БД
        schedule_text = await self._get_schedule_text_from_db()
        
        # Получаем данные из предыдущих шагов (суммаризация)
        input_data = self._get_input_for_step(['summarization', 'cleaning'])
        
        # Формируем сообщение об ошибке если нет данных
        error_message = None
        if not schedule_text:
            error_message = "📅 ⚠️ Расписание не найдено в базе данных. Загрузите фото расписания через меню анализа изображений."
            self.logger.warning(f"📅 Расписание для группы {self.context.request.chat_context.get('group_id')} не найдено")
        elif not input_data:
            error_message = "📅 ⚠️ Нет данных для анализа расписания."
            self.logger.warning("📅 Нет входных данных для анализа расписания")
        
        # Если есть ошибка, логируем её и возвращаем
        if error_message:
            # ЛОГИРУЕМ ОШИБКУ через LogSession
            if self.context.log_session:
                await self.context.log_session.log_phase(
                    "schedule_analysis", "error", error_message,
                    {
                        "log_type": log_type,
                        "has_schedule_text": bool(schedule_text),
                        "has_input_data": bool(input_data)
                    }
                )
            
            self.logger.info(f"⚠️ Анализ расписания пропущен: {error_message}")
            return error_message
        
        # Формируем промпт для анализа расписания
        schedule_prompt = self._create_schedule_analysis_prompt(input_data, schedule_text)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "schedule_analysis", "request", schedule_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        response = await self.context.provider.generate_response(schedule_prompt)
        response_time = time.time() - start_time
        
        if not response:
            error_msg = "❌ Не удалось получить анализ расписания от LLM"
            # ЛОГИРУЕМ ОШИБКУ
            if self.context.log_session:
                await self.context.log_session.log_phase(
                    "schedule_analysis", "error", error_msg,
                    {"response_time": response_time, "log_type": log_type}
                )
            raise ValueError(error_msg)
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "schedule_analysis", "response", response,
                {"response_time": response_time, "log_type": log_type}
            )
        
        self.logger.info(f"✅ Анализ расписания завершен ({len(response)} символов)")
        return response
    
    async def _do_parent_summary_with_logging(self, log_type: str) -> str:
        """Сводка для родителей с централизованным логированием"""
        self.logger.info("👨‍👩‍👧‍👦 Выполнение сводки для родителей")
        
        # Пытаемся получить результат экстракции или используем другие данные
        input_data = self._get_input_for_step(['extraction', 'classification', 'summarization'])
        
        if not input_data:
            raise ValueError("Нет данных для сводки")
        
        parent_prompt = self._create_parent_summary_prompt(input_data)
        
        # ЛОГИРУЕМ ЗАПРОС через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "parent_summary", "request", parent_prompt,
                {"log_type": log_type}
            )
        
        # Вызываем провайдер (БЕЗ логирования внутри)
        import time
        start_time = time.time()
        response = await self.context.provider.generate_response(parent_prompt)
        response_time = time.time() - start_time
        
        if not response:
            raise ValueError("Не удалось получить сводку для родителей")
        
        # ЛОГИРУЕМ ОТВЕТ через LogSession
        if self.context.log_session:
            await self.context.log_session.log_phase(
                "parent_summary", "response", response,
                {"response_time": response_time, "log_type": log_type}
            )
        
        self.logger.info(f"✅ Сводка для родителей завершена ({len(response)} символов)")
        return response

    def _build_result(self, steps: List[StepType], processing_time: float) -> AnalysisResult:
        """Формирование результата на основе выполненных шагов"""
        result_parts = []
        
        # Основная суммаризация
        if StepType.SUMMARIZATION in steps:
            summary = self.context.step_results.get('summarization', '')
            if summary:
                result_parts.append(f"📝 **Суммаризация дня:**\n{summary}")
        
        # Рефлексия и улучшение
        if StepType.IMPROVEMENT in steps:
            reflection = self.context.step_results.get('reflection', '')
            improvement = self.context.step_results.get('improvement', '')
            if reflection:
                result_parts.append(f"🤔 **Анализ и улучшения:**\n{reflection}")
            if improvement:
                result_parts.append(f"✨ **Улучшенная версия:**\n{improvement}")
        elif StepType.REFLECTION in steps:
            reflection = self.context.step_results.get('reflection', '')
            if reflection:
                result_parts.append(f"🤔 **Анализ:**\n{reflection}")
        
        # Анализ расписания
        if StepType.SCHEDULE_ANALYSIS in steps:
            schedule = self.context.step_results.get('schedule_analysis', '')
            if schedule:
                # Проверяем, является ли это сообщением об ошибке
                if schedule.startswith('📅 ⚠️') or schedule.startswith('❌'):
                    result_parts.append(f"⚠️ **Анализ расписания:**\n{schedule}")
                else:
                    result_parts.append(schedule)
        
        # Структурный анализ
        if StepType.PARENT_SUMMARY in steps:
            parent_summary = self.context.step_results.get('parent_summary', '')
            if parent_summary:
                result_parts.append(f"👨‍👩‍👧‍👦 **Сводка для родителей:**\n{parent_summary}")
        
        # Объединяем все части
        result = "\n\n".join(result_parts) if result_parts else "❌ Анализ не выполнен"
        
        return AnalysisResult(
            success=True,
            result=result,
            provider_name=self.context.request.provider_name,
            model_id=self.context.request.model_id,
            processing_time=processing_time,
            analysis_type=AnalysisType.SUMMARIZATION,
            metadata={
                'executed_steps': [s.value for s in steps],
                'step_results': dict(self.context.step_results)  # НОВОЕ
            }
        )
