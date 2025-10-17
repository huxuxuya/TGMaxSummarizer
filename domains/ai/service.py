from typing import List, Dict, Any, Optional
from .models import AnalysisRequest, AnalysisResult, ProviderInfo, AnalysisType, PipelineContext
from .pipelines import (
    SummarizationPipeline, ReflectionPipeline, 
    StructuredAnalysisPipeline, DataCleaningPipeline
)
from core.database.connection import DatabaseConnection
from core.exceptions import AIProviderError, ValidationError
import logging

logger = logging.getLogger(__name__)

class AIService:
    """Сервис для работы с AI провайдерами и анализа"""
    
    def __init__(self, db_connection: DatabaseConnection, provider_factory, config):
        self.db = db_connection
        self.provider_factory = provider_factory
        self.config = config
        
        self.pipelines = {
            AnalysisType.SUMMARIZATION: SummarizationPipeline(),
            AnalysisType.REFLECTION: ReflectionPipeline(),
            AnalysisType.STRUCTURED: StructuredAnalysisPipeline(),
            AnalysisType.CLEANING: DataCleaningPipeline()
        }
    
    async def analyze_chat(self, request: AnalysisRequest) -> AnalysisResult:
        """Выполнить анализ чата"""
        try:
            provider = await self._get_provider(request.provider_name, request.model_id)
            if not provider:
                raise AIProviderError(f"Не удалось получить провайдер {request.provider_name}")
            
            context = PipelineContext(
                request=request,
                provider=provider
            )
            
            if request.clean_data_first:
                cleaning_result = await self._run_cleaning_pipeline(context)
                if not cleaning_result.success:
                    return cleaning_result
                
                cleaned_messages = cleaning_result.metadata.get("cleaned_messages", [])
                if not cleaned_messages:
                    raise ValidationError("После очистки не осталось сообщений")
                
                context.request.messages = cleaned_messages
            
            if request.analysis_type == AnalysisType.SUMMARIZATION:
                return await self._run_summarization_pipeline(context)
            elif request.analysis_type == AnalysisType.REFLECTION:
                return await self._run_reflection_pipeline(context)
            elif request.analysis_type == AnalysisType.STRUCTURED:
                return await self._run_structured_pipeline(context)
            else:
                raise ValidationError(f"Неподдерживаемый тип анализа: {request.analysis_type}")
                
        except Exception as e:
            logger.error(f"Ошибка анализа чата: {e}")
            return AnalysisResult(
                success=False,
                error=str(e),
                provider_name=request.provider_name,
                model_id=request.model_id,
                analysis_type=request.analysis_type
            )
    
    async def _get_provider(self, provider_name: str, model_id: Optional[str] = None):
        """Получить провайдер"""
        try:
            if provider_name == 'ollama' and 'ollama' in self.config:
                provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
            else:
                provider = self.provider_factory.create_provider(provider_name, self.config)
            
            if not provider:
                return None
            
            if model_id and hasattr(provider, 'set_model'):
                provider.set_model(model_id)
            
            if not await provider.initialize():
                return None
            
            return provider
            
        except Exception as e:
            logger.error(f"Ошибка получения провайдера {provider_name}: {e}")
            return None
    
    async def _run_cleaning_pipeline(self, context: PipelineContext) -> AnalysisResult:
        """Запустить pipeline очистки"""
        pipeline = self.pipelines[AnalysisType.CLEANING]
        return await pipeline.execute(context)
    
    async def _run_summarization_pipeline(self, context: PipelineContext) -> AnalysisResult:
        """Запустить pipeline суммаризации"""
        pipeline = self.pipelines[AnalysisType.SUMMARIZATION]
        return await pipeline.execute(context)
    
    async def _run_reflection_pipeline(self, context: PipelineContext) -> AnalysisResult:
        """Запустить pipeline рефлексии"""
        summarization_pipeline = self.pipelines[AnalysisType.SUMMARIZATION]
        reflection_pipeline = self.pipelines[AnalysisType.REFLECTION]
        
        summarization_result = await summarization_pipeline.execute(context)
        if not summarization_result.success:
            return summarization_result
        
        context.step_results["summarization"] = summarization_result.result
        return await reflection_pipeline.execute(context)
    
    async def _run_structured_pipeline(self, context: PipelineContext) -> AnalysisResult:
        """Запустить pipeline структурированного анализа"""
        pipeline = self.pipelines[AnalysisType.STRUCTURED]
        return await pipeline.execute(context)
    
    async def get_available_providers(self) -> List[ProviderInfo]:
        """Получить список доступных провайдеров"""
        try:
            available_providers = []
            
            for provider_name in self.provider_factory.get_available_providers():
                if provider_name == 'ollama' and 'ollama' in self.config:
                    provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
                else:
                    provider = self.provider_factory.create_provider(provider_name, self.config)
                
                if provider:
                    is_available = await provider.is_available()
                    provider_info = provider.get_provider_info()
                    
                    available_providers.append(ProviderInfo(
                        name=provider_name,
                        display_name=provider_info.get('display_name', provider_name),
                        description=provider_info.get('description', ''),
                        available=is_available
                    ))
            
            return available_providers
            
        except Exception as e:
            logger.error(f"Ошибка получения списка провайдеров: {e}")
            return []
    
    async def validate_provider(self, provider_name: str) -> bool:
        """Валидировать провайдер"""
        try:
            provider = await self._get_provider(provider_name)
            return provider is not None
        except Exception as e:
            logger.error(f"Ошибка валидации провайдера {provider_name}: {e}")
            return False

