from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class StepType(str, Enum):
    """Типы шагов для композиционного анализа"""
    CLEANING = "cleaning"
    SUMMARIZATION = "summarization"
    REFLECTION = "reflection"
    IMPROVEMENT = "improvement"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SCHEDULE_ANALYSIS = "schedule_analysis"  # НОВОЕ: анализ расписания на завтра
    PARENT_SUMMARY = "parent_summary"

class AnalysisType(str, Enum):
    """Типы анализа (deprecated - используйте StepType)"""
    SUMMARIZATION = "summarization"
    REFLECTION = "reflection"
    STRUCTURED = "structured"
    CLEANING = "cleaning"

class AnalysisRequest(BaseModel):
    """Запрос на анализ"""
    messages: List[Dict[str, Any]]
    provider_name: str
    model_id: Optional[str] = None
    user_id: Optional[int] = None
    chat_context: Optional[Dict[str, Any]] = None
    llm_logger: Optional[Any] = None
    
    # НОВЫЙ ПОДХОД: просто список шагов
    steps: List[StepType] = Field(default_factory=lambda: [StepType.SUMMARIZATION])
    
    # Для обратной совместимости (deprecated)
    analysis_type: Optional[AnalysisType] = None
    enable_reflection: Optional[bool] = None
    clean_data_first: bool = False
    
    @validator('steps')
    def validate_steps(cls, v):
        """Валидация зависимостей шагов"""
        if StepType.IMPROVEMENT in v and StepType.REFLECTION not in v:
            raise ValueError("IMPROVEMENT требует REFLECTION")
        if not v:
            return [StepType.SUMMARIZATION]  # По умолчанию
        return v
    
    class Config:
        # Disable protected namespace warnings for model_* fields
        protected_namespaces = ()

class AnalysisResult(BaseModel):
    """Результат анализа"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    provider_name: str
    model_id: Optional[str] = None
    processing_time: Optional[float] = None
    analysis_type: AnalysisType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        # Disable protected namespace warnings for model_* fields
        protected_namespaces = ()

class ProviderInfo(BaseModel):
    """Информация о провайдере"""
    name: str
    display_name: str
    description: str
    available: bool = False
    last_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None

class PipelineStep(BaseModel):
    """Шаг pipeline"""
    name: str
    description: str
    required: bool = True
    timeout: int = 60

class PipelineContext(BaseModel):
    """Контекст выполнения pipeline"""
    request: AnalysisRequest
    provider: Any = None
    llm_logger: Optional[Any] = None
    log_session: Optional[Any] = None  # LogSession для централизованного логирования
    step_results: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

