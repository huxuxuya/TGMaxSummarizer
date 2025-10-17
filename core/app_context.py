from typing import Optional
from .config import load_config
from .database.connection import DatabaseConnection
from .state_manager import StateManager
from domains.users.service import UserService
from domains.chats.service import ChatService
from domains.ai.service import AIService
from domains.summaries.service import SummaryService
from infrastructure.ai_providers.factory import ProviderFactory

class AppContext:
    """Singleton application context для dependency injection"""
    
    _instance: Optional['AppContext'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize()
            self.__class__._initialized = True
    
    def _initialize(self):
        """Инициализация сервисов один раз"""
        self.config = load_config()
        self.db_connection = DatabaseConnection(self.config['database'].path)
        
        # Initialize services once
        self.user_service = UserService(self.db_connection)
        self.chat_service = ChatService(self.db_connection)
        self.summary_service = SummaryService(self.db_connection)
        
        provider_factory = ProviderFactory()
        providers_config = {
            name: provider.model_dump() 
            for name, provider in self.config['ai'].providers.items()
        }
        self.ai_service = AIService(
            self.db_connection, 
            provider_factory, 
            providers_config
        )
        
        # Initialize state manager
        self.state_manager = StateManager(self.db_connection)
    
    def shutdown(self):
        """Cleanup resources"""
        if hasattr(self, 'db_connection'):
            self.db_connection.close_all()

# Global accessor
def get_app_context() -> AppContext:
    return AppContext()
