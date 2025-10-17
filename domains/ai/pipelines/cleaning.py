from typing import Any
import json
import re
from .base import BasePipeline
from ..models import PipelineStep, PipelineContext, AnalysisResult, AnalysisType

class DataCleaningPipeline(BasePipeline):
    """Pipeline для очистки данных перед анализом"""
    
    def _define_steps(self):
        """Определить шаги pipeline"""
        self.steps = [
            PipelineStep(
                name="cleaning",
                description="Очистка и фильтрация сообщений",
                required=True,
                timeout=90
            )
        ]
    
    async def _execute_step(self, step: PipelineStep, context: PipelineContext) -> Any:
        """Выполнить шаг очистки"""
        if step.name == "cleaning":
            return await self._perform_cleaning(context)
        else:
            raise ValueError(f"Неизвестный шаг: {step.name}")
    
    async def _perform_cleaning(self, context: PipelineContext) -> list:
        """Выполнить очистку сообщений"""
        provider = context.provider
        messages = context.request.messages
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        if not messages:
            raise ValueError("Нет сообщений для очистки")
        
        self.logger.info(f"🧹 Начинаем очистку {len(messages)} сообщений")
        
        cleaning_prompt = self._create_cleaning_prompt(messages)
        response = await provider.generate_response(cleaning_prompt)
        
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
    
    async def _build_final_result(self, context: PipelineContext, processing_time: float) -> AnalysisResult:
        """Построить финальный результат"""
        cleaned_messages = self.get_step_result(context, "cleaning")
        
        if not cleaned_messages:
            return AnalysisResult(
                success=False,
                error="Не удалось очистить сообщения",
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=AnalysisType.CLEANING
            )
        
        original_count = len(context.request.messages)
        cleaned_count = len(cleaned_messages)
        
        return AnalysisResult(
            success=True,
            result=f"Очищено {cleaned_count} из {original_count} сообщений",
            provider_name=context.request.provider_name,
            model_id=context.request.model_id,
            processing_time=processing_time,
            analysis_type=AnalysisType.CLEANING,
            metadata={
                "original_count": original_count,
                "cleaned_count": cleaned_count,
                "filtered_count": original_count - cleaned_count,
                "cleaned_messages": cleaned_messages
            }
        )

