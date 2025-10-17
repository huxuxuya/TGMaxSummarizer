from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AnalysisType(str, Enum):
    """Типы анализа"""
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
    analysis_type: AnalysisType = AnalysisType.SUMMARIZATION
    enable_reflection: Optional[bool] = None
    clean_data_first: bool = False
    chat_context: Optional[Dict[str, Any]] = None

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
    step_results: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

