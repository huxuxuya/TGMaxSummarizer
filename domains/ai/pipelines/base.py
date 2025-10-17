from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import asyncio
from ..models import PipelineStep, PipelineContext, AnalysisResult, AnalysisType

logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    """Базовый класс для AI pipelines"""
    
    def __init__(self):
        self.steps: List[PipelineStep] = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self._define_steps()
    
    @abstractmethod
    def _define_steps(self):
        """Определить шаги pipeline"""
        pass
    
    @abstractmethod
    async def _execute_step(self, step: PipelineStep, context: PipelineContext) -> Any:
        """Выполнить конкретный шаг"""
        pass
    
    async def execute(self, context: PipelineContext) -> AnalysisResult:
        """Выполнить весь pipeline"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            self.logger.info(f"🚀 Запуск pipeline: {self.__class__.__name__}")
            
            for step in self.steps:
                self.logger.info(f"📋 Выполнение шага: {step.name}")
                
                try:
                    result = await asyncio.wait_for(
                        self._execute_step(step, context),
                        timeout=step.timeout
                    )
                    
                    context.step_results[step.name] = result
                    self.logger.info(f"✅ Шаг {step.name} выполнен успешно")
                    
                except asyncio.TimeoutError:
                    error_msg = f"Таймаут выполнения шага {step.name}"
                    self.logger.error(f"⏰ {error_msg}")
                    
                    if step.required:
                        return AnalysisResult(
                            success=False,
                            error=error_msg,
                            provider_name=context.request.provider_name,
                            model_id=context.request.model_id,
                            analysis_type=context.request.analysis_type
                        )
                    else:
                        self.logger.warning(f"⚠️ Пропускаем необязательный шаг {step.name}")
                        context.step_results[step.name] = None
                
                except Exception as e:
                    error_msg = f"Ошибка в шаге {step.name}: {str(e)}"
                    self.logger.error(f"❌ {error_msg}")
                    
                    if step.required:
                        return AnalysisResult(
                            success=False,
                            error=error_msg,
                            provider_name=context.request.provider_name,
                            model_id=context.request.model_id,
                            analysis_type=context.request.analysis_type
                        )
                    else:
                        self.logger.warning(f"⚠️ Пропускаем необязательный шаг {step.name}")
                        context.step_results[step.name] = None
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            final_result = await self._build_final_result(context, processing_time)
            self.logger.info(f"✅ Pipeline {self.__class__.__name__} выполнен за {processing_time:.2f}с")
            
            return final_result
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            error_msg = f"Критическая ошибка pipeline: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            
            return AnalysisResult(
                success=False,
                error=error_msg,
                provider_name=context.request.provider_name,
                model_id=context.request.model_id,
                processing_time=processing_time,
                analysis_type=context.request.analysis_type
            )
    
    @abstractmethod
    async def _build_final_result(self, context: PipelineContext, processing_time: float) -> AnalysisResult:
        """Построить финальный результат"""
        pass
    
    def get_step_result(self, context: PipelineContext, step_name: str) -> Any:
        """Получить результат шага"""
        return context.step_results.get(step_name)
    
    def add_metadata(self, context: PipelineContext, key: str, value: Any):
        """Добавить метаданные в контекст"""
        context.metadata[key] = value

