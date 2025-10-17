from typing import Any
import json
from .base import BasePipeline
from ..models import PipelineStep, PipelineContext, AnalysisResult, AnalysisType

class StructuredAnalysisPipeline(BasePipeline):
    """Pipeline для структурированного анализа с классификацией и экстракцией"""
    
    def _define_steps(self):
        """Определить шаги pipeline"""
        self.steps = [
            PipelineStep(
                name="classification",
                description="Классификация сообщений",
                required=True,
                timeout=120
            ),
            PipelineStep(
                name="extraction",
                description="Экстракция слотов и событий",
                required=True,
                timeout=120
            ),
            PipelineStep(
                name="parent_summary",
                description="Генерация сводки для родителей",
                required=True,
                timeout=90
            )
        ]
    
    async def _execute_step(self, step: PipelineStep, context: PipelineContext) -> Any:
        """Выполнить шаг структурированного анализа"""
        if step.name == "classification":
            return await self._perform_classification(context)
        elif step.name == "extraction":
            return await self._perform_extraction(context)
        elif step.name == "parent_summary":
            return await self._perform_parent_summary(context)
        else:
            raise ValueError(f"Неизвестный шаг: {step.name}")
    
    async def _perform_classification(self, context: PipelineContext) -> list:
        """Выполнить классификацию сообщений"""
        provider = context.provider
        messages = context.request.messages
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        if not messages:
            raise ValueError("Нет сообщений для классификации")
        
        self.logger.info(f"📊 Начинаем классификацию {len(messages)} сообщений")
        
        classification_prompt = self._create_classification_prompt(messages)
        response = await provider.generate_response(classification_prompt)
        
        if not response:
            raise ValueError("Не удалось получить классификацию")
        
        classification = self._parse_classification_response(response)
        self.logger.info(f"✅ Классификация получена: {len(classification)} сообщений")
        
        return classification
    
    async def _perform_extraction(self, context: PipelineContext) -> list:
        """Выполнить экстракцию слотов"""
        provider = context.provider
        messages = context.request.messages
        classification = self.get_step_result(context, "classification")
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        if not classification:
            raise ValueError("Нет результатов классификации")
        
        self.logger.info("🔍 Начинаем экстракцию слотов")
        
        extraction_prompt = self._create_extraction_prompt(messages, classification)
        response = await provider.generate_response(extraction_prompt)
        
        if not response:
            raise ValueError("Не удалось получить экстракцию")
        
        events = self._parse_extraction_response(response)
        self.logger.info(f"✅ Экстракция завершена: {len(events)} событий")
        
        return events
    
    async def _perform_parent_summary(self, context: PipelineContext) -> str:
        """Выполнить генерацию сводки для родителей"""
        provider = context.provider
        events = self.get_step_result(context, "extraction")
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        if not events:
            raise ValueError("Нет событий для сводки")
        
        self.logger.info("📝 Генерируем сводку для родителей")
        
        summary_prompt = self._create_parent_summary_prompt(events)
        summary = await provider.generate_response(summary_prompt)
        
        if not summary:
            raise ValueError("Не удалось получить сводку")
        
        self.logger.info(f"✅ Сводка сгенерирована ({len(summary)} символов)")
        return summary
    
    def _create_classification_prompt(self, messages: list) -> str:
        """Создать промпт для классификации"""
        messages_json = json.dumps([
            {"id": msg.get('message_id', msg.get('id', '')), "text": msg.get('text')} 
            for msg in messages
        ], ensure_ascii=False)
        
        return f"""Классифицируй следующие сообщения чата по типам:

СООБЩЕНИЯ:
{messages_json}

Классифицируй каждое сообщение по следующим категориям:
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
    
    def _create_extraction_prompt(self, messages: list, classification: list) -> str:
        """Создать промпт для экстракции"""
        classification_dict = {item.get('message_id'): item.get('class') for item in classification}
        
        messages_with_class = []
        for msg in messages:
            message_id = str(msg.get('message_id', msg.get('id', '')))
            msg_class = classification_dict.get(message_id, 'unknown')
            messages_with_class.append({
                "id": message_id,
                "text": msg.get('text'),
                "type": msg_class
            })
        
        messages_json = json.dumps(messages_with_class, ensure_ascii=False)
        
        return f"""Извлеки важные события и информацию из сообщений:

СООБЩЕНИЯ С КЛАССИФИКАЦИЕЙ:
{messages_json}

Извлеки и структурируй информацию в виде событий. Каждое событие должно содержать:
- type: тип события (rule, event, problem, coordination, etc.)
- title: краткое название
- description: описание
- importance: важность (high, medium, low)
- action_required: требуется ли действие родителей

Верни только JSON массив с объектами событий."""
    
    def _create_parent_summary_prompt(self, events: list) -> str:
        """Создать промпт для сводки родителей"""
        events_json = json.dumps(events, ensure_ascii=False, indent=2)
        
        return f"""Создай краткую и понятную сводку для родителей на основе извлеченных событий:

СОБЫТИЯ:
{events_json}

Создай структурированную сводку, которая:
1. Выделяет самое важное
2. Группирует информацию по темам
3. Указывает на необходимые действия
4. Легко читается и понимается

Используй эмодзи и четкую структуру."""
    
    def _parse_classification_response(self, response: str) -> list:
        """Парсить ответ классификации"""
        try:
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга классификации: {e}")
            return []
    
    def _parse_extraction_response(self, response: str) -> list:
        """Парсить ответ экстракции"""
        try:
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка парсинга экстракции: {e}")
            return []
    
    def _clean_json_response(self, response: str) -> str:
        """Очистить JSON ответ от markdown блоков"""
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            if end != -1:
                response = response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end != -1:
                response = response[start:end].strip()
        
        response = response.strip()
        
        start_bracket = response.find('[')
        end_bracket = response.rfind(']')
        
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            response = response[start_bracket:end_bracket + 1]
        
        return response
    
    async def _build_final_result(self, context: PipelineContext, processing_time: float) -> AnalysisResult:
        """Построить финальный результат"""
        classification = self.get_step_result(context, "classification")
        events = self.get_step_result(context, "extraction")
        summary = self.get_step_result(context, "parent_summary")
        
        if not all([classification, events, summary]):
            return AnalysisResult(
                success=False,
                error="Не все шаги структурированного анализа выполнены",
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=AnalysisType.STRUCTURED
            )
        
        return AnalysisResult(
            success=True,
            result=summary,
            provider_name=context.request.provider_name,
            model_id=context.request.model_id,
            processing_time=processing_time,
            analysis_type=AnalysisType.STRUCTURED,
            metadata={
                "classification_count": len(classification),
                "events_count": len(events),
                "summary_length": len(summary)
            }
        )

