"""
Runtime validation utilities for development mode
"""
import os
import warnings
from pydantic import BaseModel
from typing import Any

def ensure_model_attribute_access():
    """
    Monkey patch to prevent dictionary-style access on Pydantic models
    during development. Remove in production.
    
    This will warn developers when they use model['key'] instead of model.key
    """
    original_getitem = BaseModel.__getitem__
    
    def strict_getitem(self, item):
        import warnings
        warnings.warn(
            f"Using dictionary access on Pydantic model {self.__class__.__name__}. "
            f"Use '{self.__class__.__name__}.{item}' instead of '{self.__class__.__name__}['{item}']'",
            DeprecationWarning,
            stacklevel=2
        )
        return original_getitem(self, item)
    
    BaseModel.__getitem__ = strict_getitem

def setup_development_validation():
    """
    Setup development-time validation if DEV_MODE is enabled
    """
    if os.environ.get('DEV_MODE') == 'true':
        ensure_model_attribute_access()
        print("🔧 Development mode: Pydantic model validation enabled")
