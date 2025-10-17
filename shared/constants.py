from enum import Enum

class CallbackActions(str, Enum):
    """Действия callback кнопок"""
    MANAGE_CHATS = "manage_chats"
    STATISTICS = "statistics"
    SELECT_AI_PROVIDER = "select_ai_provider"
    SETTINGS = "settings"
    CHANGE_GROUP = "change_group"
    ADD_CHAT = "add_chat"
    REMOVE_CHAT = "remove_chat"
    LIST_CHATS = "list_chats"
    CHAT_SETTINGS = "chat_settings"
    BACK_TO_MAIN = "back_to_main"
    BACK_TO_MANAGE_CHATS = "back_to_manage_chats"
    BACK_TO_CHAT_SETTINGS = "back_to_chat_settings"
    CANCEL = "cancel"
    CONFIRM = "confirm"

class MessageTypes(str, Enum):
    """Типы сообщений"""
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"
    STICKER = "sticker"

class AnalysisTypes(str, Enum):
    """Типы анализа"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    STRUCTURED = "structured"

MAX_MESSAGE_LENGTH = 4096
MAX_MESSAGES_PER_LOAD = 1000
DEFAULT_TIMEOUT = 30

