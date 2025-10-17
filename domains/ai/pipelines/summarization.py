from typing import Any
from .base import BasePipeline
from ..models import PipelineStep, PipelineContext, AnalysisResult, AnalysisType

class SummarizationPipeline(BasePipeline):
    """Pipeline для базовой суммаризации"""
    
    def _define_steps(self):
        """Определить шаги pipeline"""
        self.steps = [
            PipelineStep(
                name="summarization",
                description="Генерация суммаризации чата",
                required=True,
                timeout=120
            )
        ]
    
    async def _execute_step(self, step: PipelineStep, context: PipelineContext) -> Any:
        """Выполнить шаг суммаризации"""
        if step.name == "summarization":
            return await self._perform_summarization(context)
        else:
            raise ValueError(f"Неизвестный шаг: {step.name}")
    
    async def _perform_summarization(self, context: PipelineContext) -> str:
        """Выполнить суммаризацию"""
        provider = context.provider
        messages = context.request.messages
        chat_context = context.request.chat_context or {}
        
        if not provider:
            raise ValueError("Провайдер не инициализирован")
        
        if not messages:
            raise ValueError("Нет сообщений для анализа")
        
        self.logger.info(f"📝 Начинаем суммаризацию {len(messages)} сообщений")
        
        summary = await provider.summarize_chat(messages, chat_context)
        
        if not summary:
            raise ValueError("Не удалось получить суммаризацию")
        
        self.logger.info(f"✅ Суммаризация получена ({len(summary)} символов)")
        return summary
    
    async def _build_final_result(self, context: PipelineContext, processing_time: float) -> AnalysisResult:
        """Построить финальный результат"""
        summary = self.get_step_result(context, "summarization")
        
        if not summary:
            return AnalysisResult(
                success=False,
                error="Не удалось получить суммаризацию",
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=AnalysisType.SUMMARIZATION
            )
        
        return AnalysisResult(
            success=True,
            result=summary,
            provider_name=context.request.provider_name,
            model_id=context.request.model_id,
            processing_time=processing_time,
            analysis_type=AnalysisType.SUMMARIZATION,
            metadata={
                "messages_count": len(context.request.messages),
                "summary_length": len(summary)
            }
        )

