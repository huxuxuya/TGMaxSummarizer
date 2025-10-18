from typing import Any
from .base import BasePipeline
from ..models import PipelineStep, PipelineContext, AnalysisResult, AnalysisType

class ReflectionPipeline(BasePipeline):
    """Pipeline для рефлексии и улучшения суммаризации"""
    
    def _define_steps(self):
        """Определить шаги pipeline"""
        self.steps = [
            PipelineStep(
                name="reflection",
                description="Анализ и рефлексия над суммаризацией",
                required=True,
                timeout=90
            ),
            PipelineStep(
                name="improvement",
                description="Улучшение суммаризации на основе рефлексии",
                required=True,
                timeout=90
            )
        ]
    
    async def _execute_step(self, step: PipelineStep, context: PipelineContext) -> Any:
        """Выполнить шаг рефлексии"""
        if step.name == "reflection":
            return await self._perform_reflection(context)
        elif step.name == "improvement":
            return await self._perform_improvement(context)
        else:
            raise ValueError(f"Неизвестный шаг: {step.name}")
    
    async def _perform_reflection(self, context: PipelineContext) -> str:
        """Выполнить рефлексию"""
        provider = context.provider
        summary = context.step_results.get("summarization")
        
        if not summary:
            raise ValueError("Нет суммаризации для рефлексии")
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        self.logger.info("🤔 Начинаем рефлексию над суммаризацией")
        
        reflection_prompt = self._create_reflection_prompt(summary, context)
        reflection = await provider.generate_response(reflection_prompt)
        
        if not reflection:
            raise ValueError("Не удалось получить рефлексию")
        
        self.logger.info(f"✅ Рефлексия получена ({len(reflection)} символов)")
        return reflection
    
    async def _perform_improvement(self, context: PipelineContext) -> str:
        """Выполнить улучшение суммаризации"""
        provider = context.provider
        original_summary = context.step_results.get("summarization")
        reflection = context.step_results.get("reflection")
        
        if not original_summary or not reflection:
            raise ValueError("Нет данных для улучшения")
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        self.logger.info("✨ Начинаем улучшение суммаризации")
        
        improvement_prompt = self._create_improvement_prompt(original_summary, reflection)
        improved_summary = await provider.generate_response(improvement_prompt)
        
        if not improved_summary:
            raise ValueError("Не удалось получить улучшенную суммаризацию")
        
        self.logger.info(f"✅ Улучшенная суммаризация получена ({len(improved_summary)} символов)")
        return improved_summary
    
    def _create_reflection_prompt(self, summary: str, context: PipelineContext) -> str:
        """Создать промпт для рефлексии"""
        messages = context.request.messages
        total_messages = len(messages)
        date = context.request.chat_context.get('date', 'неизвестная дата') if context.request.chat_context else 'неизвестная дата'
        
        # Форматируем исходные сообщения для анализа
        # Ограничиваем количество для экономии токенов (первые 50 сообщений)
        max_messages = min(50, total_messages)
        formatted_messages = ""
        
        for i, msg in enumerate(messages[:max_messages]):
            message_id = msg.get('id', i + 1)
            text = msg.get('text', '').strip()
            sender = msg.get('sender', 'Неизвестный')
            
            if text:
                # Компактный формат для экономии токенов
                formatted_messages += f"{i+1}. [{sender}]: {text}\n"
        
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
    
    async def _build_final_result(self, context: PipelineContext, processing_time: float) -> AnalysisResult:
        """Построить финальный результат"""
        summary = context.step_results.get("summarization")
        reflection = self.get_step_result(context, "reflection")
        improved = self.get_step_result(context, "improvement")
        
        if not summary:
            return AnalysisResult(
                success=False,
                error="Нет исходной суммаризации",
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=AnalysisType.REFLECTION
            )
        
        if not reflection:
            return AnalysisResult(
                success=False,
                error="Не удалось выполнить рефлексию",
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=AnalysisType.REFLECTION
            )
        
        result_text = f"📝 Исходная суммаризация:\n{summary}\n\n"
        result_text += f"🤔 Рефлексия и анализ:\n{reflection}\n\n"
        result_text += f"✨ Улучшенная суммаризация:\n{improved}"
        
        return AnalysisResult(
            success=True,
            result=result_text,
            provider_name=context.request.provider_name,
            model_id=context.request.model_id,
            processing_time=processing_time,
            analysis_type=AnalysisType.REFLECTION,
            metadata={
                "has_reflection": bool(reflection),
                "has_improvement": bool(improved),
                "original_length": len(summary),
                "reflection_length": len(reflection) if reflection else 0,
                "improved_length": len(improved) if improved else 0
            }
        )

