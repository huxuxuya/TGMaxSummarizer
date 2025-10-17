from typing import List, Dict, Any, Optional
from core.database.base_repository import BaseRepository
from .models import Chat, Message, ChatStats, Group, GroupUser, GroupVKChat
import json

class ChatRepository(BaseRepository):
    """Репозиторий для работы с чатами VK MAX"""
    
    def _table_name(self) -> str:
        return "vk_chats"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS vk_chats (
                chat_id TEXT PRIMARY KEY,
                chat_name TEXT,
                chat_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    
    def add_chat(self, chat: Chat) -> bool:
        """Добавить чат"""
        query = """
            INSERT OR REPLACE INTO vk_chats (chat_id, chat_name, chat_type)
            VALUES (?, ?, ?)
        """
        affected = self.execute_update(query, (chat.chat_id, chat.chat_name, chat.chat_type.value))
        return affected > 0
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Получить чат по ID"""
        query = "SELECT * FROM vk_chats WHERE chat_id = ?"
        results = self.execute_query(query, (chat_id,))
        if results:
            return Chat(**results[0])
        return None
    
    def remove_chat(self, chat_id: str) -> bool:
        """Удалить чат"""
        query = "DELETE FROM vk_chats WHERE chat_id = ?"
        affected = self.execute_update(query, (chat_id,))
        return affected > 0

class MessageRepository(BaseRepository):
    """Репозиторий для работы с сообщениями"""
    
    def _table_name(self) -> str:
        return "messages"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_chat_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                sender_id INTEGER,
                sender_name TEXT,
                text TEXT,
                message_time INTEGER,
                date TEXT,
                message_type TEXT,
                attachments TEXT,
                reaction_info TEXT,
                image_paths TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(vk_chat_id, message_id)
            )
        """
    
    def save_messages(self, messages: List[Message]) -> int:
        """Сохранить сообщения"""
        query = """
            INSERT OR IGNORE INTO messages (
                vk_chat_id, message_id, sender_id, sender_name, text,
                message_time, date, message_type, attachments, reaction_info, image_paths
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params_list = []
        for msg in messages:
            params_list.append((
                msg.vk_chat_id,
                msg.message_id,
                msg.sender_id,
                msg.sender_name,
                msg.text,
                msg.message_time,
                msg.date,
                msg.message_type.value,
                json.dumps(msg.attachments),
                json.dumps(msg.reaction_info),
                json.dumps(msg.image_paths)
            ))
        
        return self.execute_many(query, params_list)
    
    def get_messages_by_date(self, vk_chat_id: str, date: str) -> List[Message]:
        """Получить сообщения за определенную дату"""
        query = """
            SELECT message_id, sender_id, sender_name, text, message_time, 
                   message_type, attachments, reaction_info, image_paths
            FROM messages 
            WHERE vk_chat_id = ? AND date = ?
            ORDER BY message_time ASC
        """
        results = self.execute_query(query, (vk_chat_id, date))
        
        messages = []
        for row in results:
            message = Message(
                message_id=row['message_id'],
                vk_chat_id=vk_chat_id,
                sender_id=row['sender_id'],
                sender_name=row['sender_name'],
                text=row['text'],
                message_time=row['message_time'],
                date=date,
                message_type=row['message_type'],
                attachments=json.loads(row['attachments']) if row['attachments'] else [],
                reaction_info=json.loads(row['reaction_info']) if row['reaction_info'] else {},
                image_paths=json.loads(row['image_paths']) if row['image_paths'] else []
            )
            messages.append(message)
        
        return messages
    
    def get_last_message_timestamp(self, vk_chat_id: str) -> Optional[int]:
        """Получить timestamp последнего сообщения в чате"""
        query = """
            SELECT message_time FROM messages 
            WHERE vk_chat_id = ? 
            ORDER BY message_time DESC 
            LIMIT 1
        """
        results = self.execute_query(query, (vk_chat_id,))
        return results[0]['message_time'] if results else None
    
    def get_chat_stats(self, vk_chat_id: str) -> ChatStats:
        """Получить статистику чата"""
        total_query = "SELECT COUNT(*) as count FROM messages WHERE vk_chat_id = ?"
        days_query = "SELECT COUNT(DISTINCT date) as count FROM messages WHERE vk_chat_id = ?"
        recent_query = """
            SELECT date, COUNT(*) as message_count
            FROM messages 
            WHERE vk_chat_id = ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT 5
        """
        
        total_result = self.execute_query(total_query, (vk_chat_id,))
        days_result = self.execute_query(days_query, (vk_chat_id,))
        recent_result = self.execute_query(recent_query, (vk_chat_id,))
        
        return ChatStats(
            vk_chat_id=vk_chat_id,
            total_messages=total_result[0]['count'] if total_result else 0,
            days_count=days_result[0]['count'] if days_result else 0,
            recent_days=[{"date": row['date'], "count": row['message_count']} for row in recent_result]
        )

class GroupRepository(BaseRepository):
    """Репозиторий для работы с Telegram группами"""
    
    def _table_name(self) -> str:
        return "groups"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT,
                schedule_photo_file_id TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
    
    def add_group(self, group: Group) -> bool:
        """Добавить группу"""
        query = """
            INSERT OR REPLACE INTO groups (group_id, group_name, schedule_photo_file_id)
            VALUES (?, ?, ?)
        """
        affected = self.execute_update(query, (group.group_id, group.group_name, group.schedule_photo_file_id))
        return affected > 0
    
    def get_group(self, group_id: int) -> Optional[Group]:
        """Получить группу по ID"""
        query = "SELECT * FROM groups WHERE group_id = ?"
        results = self.execute_query(query, (group_id,))
        if results:
            return Group(**results[0])
        return None
    
    def get_all_groups(self) -> List[Group]:
        """Получить все группы"""
        query = "SELECT group_id, group_name, schedule_photo_file_id FROM groups ORDER BY group_name"
        results = self.execute_query(query)
        return [Group(**row) for row in results]
    
    def set_schedule_photo(self, group_id: int, file_id: str) -> bool:
        """Установить фото расписания для группы"""
        query = "UPDATE groups SET schedule_photo_file_id = ? WHERE group_id = ?"
        affected = self.execute_update(query, (file_id, group_id))
        return affected > 0
    
    def get_schedule_photo(self, group_id: int) -> Optional[str]:
        """Получить file_id фото расписания группы"""
        query = "SELECT schedule_photo_file_id FROM groups WHERE group_id = ?"
        results = self.execute_query(query, (group_id,))
        return results[0]['schedule_photo_file_id'] if results and results[0]['schedule_photo_file_id'] else None
    
    def delete_schedule_photo(self, group_id: int) -> bool:
        """Удалить фото расписания группы"""
        query = "UPDATE groups SET schedule_photo_file_id = NULL WHERE group_id = ?"
        affected = self.execute_update(query, (group_id,))
        return affected > 0

class GroupUserRepository(BaseRepository):
    """Репозиторий для связи пользователей с группами"""
    
    def _table_name(self) -> str:
        return "group_users"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS group_users (
                group_id INTEGER,
                user_id INTEGER,
                is_admin BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (group_id, user_id)
            )
        """
    
    def add_group_user(self, group_user: GroupUser) -> bool:
        """Добавить пользователя в группу"""
        query = """
            INSERT OR REPLACE INTO group_users (group_id, user_id, is_admin)
            VALUES (?, ?, ?)
        """
        affected = self.execute_update(query, (group_user.group_id, group_user.user_id, group_user.is_admin))
        return affected > 0
    
    def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить группы пользователя"""
        query = """
            SELECT g.group_id, g.group_name, gu.is_admin
            FROM groups g
            JOIN group_users gu ON g.group_id = gu.group_id
            WHERE gu.user_id = ?
        """
        results = self.execute_query(query, (user_id,))
        return [{"group_id": row['group_id'], "group_name": row['group_name'], "is_admin": bool(row['is_admin'])} for row in results]

class GroupVKChatRepository(BaseRepository):
    """Репозиторий для связи групп с чатами VK MAX"""
    
    def _table_name(self) -> str:
        return "group_vk_chats"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS group_vk_chats (
                group_id INTEGER,
                vk_chat_id TEXT,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, vk_chat_id)
            )
        """
    
    def add_group_vk_chat(self, group_vk_chat: GroupVKChat) -> bool:
        """Связать группу с чатом VK MAX"""
        query = """
            INSERT OR REPLACE INTO group_vk_chats (group_id, vk_chat_id, added_by)
            VALUES (?, ?, ?)
        """
        affected = self.execute_update(query, (group_vk_chat.group_id, group_vk_chat.vk_chat_id, group_vk_chat.added_by))
        return affected > 0
    
    def get_group_vk_chats(self, group_id: int) -> List[Dict[str, Any]]:
        """Получить чаты VK MAX для группы"""
        query = """
            SELECT vc.chat_id, vc.chat_name, vc.chat_type
            FROM vk_chats vc
            JOIN group_vk_chats gvc ON vc.chat_id = gvc.vk_chat_id
            WHERE gvc.group_id = ?
        """
        return self.execute_query(query, (group_id,))
    
    def remove_group_vk_chat(self, group_id: int, vk_chat_id: str) -> bool:
        """Удалить связь группы с чатом VK MAX"""
        query = "DELETE FROM group_vk_chats WHERE group_id = ? AND vk_chat_id = ?"
        affected = self.execute_update(query, (group_id, vk_chat_id))
        return affected > 0
