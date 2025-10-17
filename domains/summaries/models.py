from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SummaryType(str, Enum):
    """Типы суммаризаций"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class Summary(BaseModel):
    """Модель суммаризации"""
    id: Optional[int] = None
    vk_chat_id: str
    date: str
    summary_text: str
    reflection_text: Optional[str] = None
    improved_summary_text: Optional[str] = None
    summary_type: SummaryType = SummaryType.DAILY
    provider_name: str = "gigachat"
    provider_version: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SummaryInfo(BaseModel):
    """Summary metadata for listings"""
    date: str
    summary_type: SummaryType
    count: int
    created_at: Optional[datetime] = None

class SummaryResult(BaseModel):
    """Результат анализа с рефлексией и улучшением"""
    summary: str
    reflection: Optional[str] = None
    improved: Optional[str] = None
    display_text: str
    display_text_alt: Optional[str] = None
    events: Optional[list] = None
    classification: Optional[list] = None

