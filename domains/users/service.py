from typing import List, Optional
from .models import User, UserPreferences, UserGroup
from .repository import UserRepository, UserPreferencesRepository, UserOpenRouterRepository
from ..chats.repository import GroupUserRepository
from core.database.connection import DatabaseConnection
from core.exceptions import ValidationError

class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.user_repo = UserRepository(db_connection)
        self.preferences_repo = UserPreferencesRepository(db_connection)
        self.openrouter_repo = UserOpenRouterRepository(db_connection)
        self.group_user_repo = GroupUserRepository(db_connection)
        
        self.user_repo.create_table()
        self.preferences_repo.create_table()
        self.openrouter_repo.create_table()
        self.group_user_repo.create_table()
    
    def create_or_update_user(self, user_id: int, username: str = None, is_admin: bool = False) -> User:
        """Создать или обновить пользователя"""
        user = User(
            user_id=user_id,
            username=username,
            is_admin=is_admin
        )
        
        if not self.user_repo.add_user(user):
            raise ValidationError(f"Не удалось сохранить пользователя {user_id}")
        
        return user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя"""
        return self.user_repo.get_user(user_id)
    
    def get_user_groups(self, user_id: int) -> List[UserGroup]:
        """Получить группы пользователя"""
        groups_data = self.group_user_repo.get_user_groups(user_id)
        return [UserGroup(group_id=group['group_id'], group_name=group['group_name'], is_admin=group['is_admin']) for group in groups_data]
    
    def is_user_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь админом"""
        return self.user_repo.is_user_admin(user_id)
    
    def get_user_preferences(self, user_id: int) -> UserPreferences:
        """Получить предпочтения пользователя"""
        preferences = self.preferences_repo.get_preferences(user_id)
        if not preferences:
            preferences = UserPreferences(user_id=user_id)
            self.preferences_repo.save_preferences(preferences)
        return preferences
    
    def update_user_preferences(self, preferences: UserPreferences) -> bool:
        """Обновить предпочтения пользователя"""
        return self.preferences_repo.save_preferences(preferences)
    
    def set_user_openrouter_model(self, user_id: int, model_id: str) -> bool:
        """Установить модель OpenRouter для пользователя"""
        return self.openrouter_repo.set_user_model(user_id, model_id)
    
    def get_user_openrouter_model(self, user_id: int) -> str:
        """Получить модель OpenRouter пользователя"""
        return self.openrouter_repo.get_user_model(user_id)
