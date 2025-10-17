from typing import List, Optional
from .models import User, UserPreferences, UserGroup
from .repository import UserRepository, UserPreferencesRepository, UserOpenRouterRepository, UserLastChatRepository
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
        self.last_chat_repo = UserLastChatRepository(db_connection)
        
        self.user_repo.create_table()
        self.preferences_repo.create_table()
        self.openrouter_repo.create_table()
        self.group_user_repo.create_table()
        self.last_chat_repo.create_table()
    
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
    
    def set_last_chat(self, user_id: int, group_id: int, chat_id: str) -> bool:
        """Установить последний открытый чат для пользователя в группе"""
        return self.last_chat_repo.set_last_chat(user_id, group_id, chat_id)
    
    def get_last_chat(self, user_id: int, group_id: int) -> Optional[str]:
        """Получить последний открытый чат для пользователя в группе"""
        return self.last_chat_repo.get_last_chat(user_id, group_id)
    
    def load_user_preferences_to_context(self, user_id: int, context) -> None:
        """Загрузить предпочтения пользователя в context.user_data"""
        preferences = self.get_user_preferences(user_id)
        if preferences:
            print(f"🔍 DEBUG: load_user_preferences_to_context для user_id {user_id}:")
            print(f"   confirmed_provider: {preferences.confirmed_provider}")
            print(f"   selected_model_id: {preferences.selected_model_id}")
            print(f"   default_scenario: {preferences.default_scenario}")
            
            context.user_data['confirmed_provider'] = preferences.confirmed_provider
            context.user_data['selected_model_id'] = preferences.selected_model_id
            context.user_data['default_scenario'] = preferences.default_scenario
        else:
            print(f"🔍 DEBUG: Нет предпочтений для user_id {user_id}")
    
    def save_user_ai_settings(self, user_id: int, provider: str = None, model_id: str = None, scenario: str = None) -> bool:
        """Сохранить настройки AI пользователя (частичное обновление)"""
        preferences = self.get_user_preferences(user_id)
        if not preferences:
            preferences = UserPreferences(user_id=user_id)

        # Обновляем только переданные параметры
        if provider is not None:
            preferences.confirmed_provider = provider
        if model_id is not None:
            preferences.selected_model_id = model_id
        if scenario is not None:
            preferences.default_scenario = scenario

        return self.update_user_preferences(preferences)
    
    def clear_user_ai_settings(self, user_id: int) -> bool:
        """Очистить настройки AI пользователя"""
        try:
            self.preferences_repo.delete_preferences(user_id)
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки настроек пользователя {user_id}: {e}")
            return False