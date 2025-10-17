from typing import List, Dict, Any, Optional
from .models import Chat, Message, ChatStats, Group, GroupUser, GroupVKChat
from .repository import (
    ChatRepository, MessageRepository, GroupRepository, 
    GroupUserRepository, GroupVKChatRepository
)
from core.database.connection import DatabaseConnection
from core.exceptions import ValidationError

class ChatService:
    """Сервис для работы с чатами и сообщениями"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.chat_repo = ChatRepository(db_connection)
        self.message_repo = MessageRepository(db_connection)
        self.group_repo = GroupRepository(db_connection)
        self.group_user_repo = GroupUserRepository(db_connection)
        self.group_vk_chat_repo = GroupVKChatRepository(db_connection)
        
        self.chat_repo.create_table()
        self.message_repo.create_table()
        self.group_repo.create_table()
        self.group_user_repo.create_table()
        self.group_vk_chat_repo.create_table()
    
    def add_chat(self, chat: Chat) -> bool:
        """Добавить чат VK MAX"""
        return self.chat_repo.add_chat(chat)
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Получить чат по ID"""
        return self.chat_repo.get_chat(chat_id)
    
    def remove_chat(self, chat_id: str) -> bool:
        """Удалить чат"""
        return self.chat_repo.remove_chat(chat_id)
    
    def save_messages(self, messages_data: List[Dict[str, Any]]) -> int:
        """Сохранить сообщения"""
        from .models import Message, MessageType
        
        messages = []
        for msg_data in messages_data:
            message = Message(
                message_id=msg_data["message_id"],
                vk_chat_id=msg_data["vk_chat_id"],
                sender_id=msg_data.get("sender_id"),
                sender_name=msg_data.get("sender_name"),
                text=msg_data.get("text", ""),
                message_time=msg_data.get("message_time"),
                date=msg_data.get("date", ""),
                message_type=MessageType(msg_data.get("message_type", "USER")),
                attachments=msg_data.get("attachments", []),
                reaction_info=msg_data.get("reaction_info", {}),
                image_paths=msg_data.get("image_paths", [])
            )
            messages.append(message)
        
        return self.message_repo.save_messages(messages)
    
    def get_messages_by_date(self, vk_chat_id: str, date: str) -> List[Message]:
        """Получить сообщения за определенную дату"""
        return self.message_repo.get_messages_by_date(vk_chat_id, date)
    
    def get_last_message_timestamp(self, vk_chat_id: str) -> Optional[int]:
        """Получить timestamp последнего сообщения"""
        return self.message_repo.get_last_message_timestamp(vk_chat_id)
    
    def get_chat_stats(self, vk_chat_id: str) -> ChatStats:
        """Получить статистику чата"""
        return self.message_repo.get_chat_stats(vk_chat_id)
    
    def add_group(self, group: Group) -> bool:
        """Добавить Telegram группу"""
        return self.group_repo.add_group(group)
    
    def get_group(self, group_id: int) -> Optional[Group]:
        """Получить группу по ID"""
        return self.group_repo.get_group(group_id)
    
    def get_all_groups(self) -> List[Group]:
        """Получить все группы"""
        return self.group_repo.get_all_groups()
    
    def set_schedule_photo(self, group_id: int, file_id: str) -> bool:
        """Установить фото расписания"""
        return self.group_repo.set_schedule_photo(group_id, file_id)
    
    def get_schedule_photo(self, group_id: int) -> Optional[str]:
        """Получить фото расписания"""
        return self.group_repo.get_schedule_photo(group_id)
    
    def delete_schedule_photo(self, group_id: int) -> bool:
        """Удалить фото расписания"""
        return self.group_repo.delete_schedule_photo(group_id)
    
    def add_group_user(self, group_user: GroupUser) -> bool:
        """Добавить пользователя в группу"""
        return self.group_user_repo.add_group_user(group_user)
    
    def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить группы пользователя"""
        return self.group_user_repo.get_user_groups(user_id)
    
    def add_group_vk_chat(self, group_vk_chat: GroupVKChat) -> bool:
        """Связать группу с чатом VK MAX"""
        return self.group_vk_chat_repo.add_group_vk_chat(group_vk_chat)
    
    def get_group_vk_chats(self, group_id: int) -> List[Dict[str, Any]]:
        """Получить чаты VK MAX для группы"""
        return self.group_vk_chat_repo.get_group_vk_chats(group_id)
    
    def remove_group_vk_chat(self, group_id: int, vk_chat_id: str) -> bool:
        """Удалить связь группы с чатом VK MAX"""
        return self.group_vk_chat_repo.remove_group_vk_chat(group_id, vk_chat_id)
    
    def get_last_message_timestamp(self, vk_chat_id: str) -> Optional[str]:
        """Получить timestamp последнего сообщения в чате"""
        return self.message_repo.get_last_message_timestamp(vk_chat_id)

