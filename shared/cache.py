"""
Простое кэширование для ускорения работы бота
"""
import time
import threading
from typing import Any, Optional, Dict
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SimpleCache:
    """Простой кэш с TTL (Time To Live)"""
    
    def __init__(self, default_ttl: int = 300):  # 5 минут по умолчанию
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша с автоматической десериализацией Pydantic моделей"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() > entry['expires_at']:
                del self._cache[key]
                return None
            
            # Автоматическая десериализация Pydantic моделей
            value = entry['value']
            model_info = entry.get('model_info')
            
            if model_info:
                try:
                    module_name, class_name = model_info['class'].rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    model_class = getattr(module, class_name)
                    
                    if model_info['type'] == 'pydantic':
                        return model_class(**value)
                    elif model_info['type'] == 'pydantic_list':
                        return [model_class(**item) for item in value]
                except Exception as e:
                    logger.warning(f"Failed to deserialize Pydantic model from cache: {e}")
                    # Fallback to raw value
                    return value
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Сохранить значение в кэш с автоматической сериализацией Pydantic моделей"""
        with self._lock:
            if ttl is None:
                ttl = self.default_ttl
            
            # Автоматическая сериализация Pydantic моделей и списков моделей
            cached_value = value
            model_info = None
            
            if isinstance(value, BaseModel):
                cached_value = value.model_dump()
                model_info = {'type': 'pydantic', 'class': f"{value.__class__.__module__}.{value.__class__.__name__}"}
            elif isinstance(value, list) and value and isinstance(value[0], BaseModel):
                cached_value = [item.model_dump() for item in value]
                model_info = {'type': 'pydantic_list', 'class': f"{value[0].__class__.__module__}.{value[0].__class__.__name__}"}
            
            self._cache[key] = {
                'value': cached_value,
                'model_info': model_info,
                'expires_at': time.time() + ttl
            }
    
    def delete(self, key: str) -> None:
        """Удалить значение из кэша"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Очистить весь кэш"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Удалить истекшие записи и вернуть количество удаленных"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)

# Глобальный экземпляр кэша
cache = SimpleCache(default_ttl=300)  # 5 минут

def cached(ttl: int = 300):
    """Декоратор для кэширования результатов функций"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Создаем ключ кэша на основе аргументов функции
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Пытаемся получить из кэша
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Выполняем функцию и кэшируем результат
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {func.__name__}, cached result")
            
            return result
        return wrapper
    return decorator
