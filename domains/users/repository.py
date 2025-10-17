from typing import List, Dict, Any, Optional
from core.database.base_repository import BaseRepository
from .models import User, UserPreferences
import json

class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями"""
    
    def _table_name(self) -> str:
        return "users"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    
    def add_user(self, user: User) -> bool:
        """Добавить пользователя"""
        query = """
            INSERT OR REPLACE INTO users (user_id, username, is_admin)
            VALUES (?, ?, ?)
        """
        affected = self.execute_update(query, (user.user_id, user.username, user.is_admin))
        return affected > 0
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        query = "SELECT * FROM users WHERE user_id = ?"
        results = self.execute_query(query, (user_id,))
        if results:
            return User(**results[0])
        return None
    
    
    def is_user_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь админом"""
        user = self.get_user(user_id)
        return user.is_admin if user else False

class UserPreferencesRepository(BaseRepository):
    """Репозиторий для предпочтений пользователей"""
    
    def _table_name(self) -> str:
        return "user_ai_preferences"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS user_ai_preferences (
                user_id INTEGER PRIMARY KEY,
                default_provider TEXT DEFAULT 'gigachat',
                preferred_providers TEXT DEFAULT '["gigachat"]',
                ollama_model TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
    
    def save_preferences(self, preferences: UserPreferences) -> bool:
        """Сохранить предпочтения пользователя"""
        query = """
            INSERT OR REPLACE INTO user_ai_preferences 
            (user_id, default_provider, preferred_providers, ollama_model, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        preferred_providers_json = json.dumps(preferences.preferred_providers)
        affected = self.execute_update(query, (
            preferences.user_id,
            preferences.default_provider,
            preferred_providers_json,
            preferences.ollama_model
        ))
        return affected > 0
    
    def get_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Получить предпочтения пользователя"""
        query = """
            SELECT default_provider, preferred_providers, ollama_model
            FROM user_ai_preferences
            WHERE user_id = ?
        """
        results = self.execute_query(query, (user_id,))
        if results:
            row = results[0]
            try:
                preferred_providers = json.loads(row['preferred_providers']) if row['preferred_providers'] else ['gigachat']
            except json.JSONDecodeError:
                preferred_providers = ['gigachat']
            
            return UserPreferences(
                user_id=user_id,
                default_provider=row['default_provider'] or 'gigachat',
                preferred_providers=preferred_providers,
                ollama_model=row['ollama_model']
            )
        return None

class UserOpenRouterRepository(BaseRepository):
    """Репозиторий для моделей OpenRouter пользователей"""
    
    def _table_name(self) -> str:
        return "user_openrouter_models"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS user_openrouter_models (
                user_id INTEGER PRIMARY KEY,
                selected_model TEXT DEFAULT 'deepseek/deepseek-chat-v3.1:free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
    
    def set_user_model(self, user_id: int, model_id: str) -> bool:
        """Установить модель OpenRouter для пользователя"""
        query = """
            INSERT OR REPLACE INTO user_openrouter_models 
            (user_id, selected_model, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """
        affected = self.execute_update(query, (user_id, model_id))
        return affected > 0
    
    def get_user_model(self, user_id: int) -> str:
        """Получить выбранную модель OpenRouter для пользователя"""
        query = """
            SELECT selected_model FROM user_openrouter_models
            WHERE user_id = ?
        """
        results = self.execute_query(query, (user_id,))
        if results:
            return results[0]['selected_model']
        return 'deepseek/deepseek-chat-v3.1:free'
