from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class User(BaseModel):
    """Модель пользователя"""
    user_id: int
    username: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserPreferences(BaseModel):
    """Предпочтения пользователя для AI провайдеров"""
    user_id: int
    default_provider: str = "gigachat"
    preferred_providers: List[str] = Field(default_factory=lambda: ["gigachat"])
    ollama_model: Optional[str] = None
    openrouter_model: str = "deepseek/deepseek-chat-v3.1:free"
    confirmed_provider: str = "openrouter"  # NEW
    selected_model_id: Optional[str] = None  # NEW
    default_scenario: str = "fast"  # NEW - modular for easy expansion
    custom_steps: Optional[str] = None  # NEW - JSON string with custom pipeline steps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserGroup(BaseModel):
    """Связь пользователя с группой"""
    group_id: int
    group_name: str
    is_admin: bool = False

