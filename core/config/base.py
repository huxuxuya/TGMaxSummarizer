from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import os

class BaseConfig(BaseModel):
    """Базовая конфигурация с общими настройками"""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        validate_assignment = True

