"""
Модуль для работы с SQLite базой данных
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Менеджер базы данных для Telegram бота"""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Инициализация базы данных - создание всех таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Пользователи бота
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Telegram группы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    group_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Связь пользователей с группами
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_users (
                    group_id INTEGER,
                    user_id INTEGER,
                    is_admin BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (group_id, user_id)
                )
            """)
            
            # Чаты VK MAX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vk_chats (
                    chat_id TEXT PRIMARY KEY,
                    chat_name TEXT,
                    chat_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Связь групп с чатами VK MAX
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_vk_chats (
                    group_id INTEGER,
                    vk_chat_id TEXT,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, vk_chat_id)
                )
            """)
            
            # Сообщения по дням
            cursor.execute("""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vk_chat_id, message_id)
                )
            """)
            
            # Статистика по дням
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    vk_chat_id TEXT,
                    date TEXT,
                    message_count INTEGER,
                    unique_senders INTEGER,
                    first_message_time INTEGER,
                    last_message_time INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (vk_chat_id, date)
                )
            """)
            
            # Суммаризации
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vk_chat_id TEXT,
                    date TEXT,
                    summary_text TEXT,
                    reflection_text TEXT,
                    improved_summary_text TEXT,
                    summary_type TEXT DEFAULT 'daily',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vk_chat_id, date, summary_type)
                )
            """)
            
            # Миграция: добавляем новые поля если их нет
            try:
                cursor.execute("ALTER TABLE summaries ADD COLUMN reflection_text TEXT")
            except sqlite3.OperationalError:
                pass  # Поле уже существует
            
            try:
                cursor.execute("ALTER TABLE summaries ADD COLUMN improved_summary_text TEXT")
            except sqlite3.OperationalError:
                pass  # Поле уже существует
            
            # Сообщения бота в группах
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    group_id INTEGER,
                    vk_chat_id TEXT,
                    date TEXT,
                    message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, vk_chat_id, date)
                )
            """)
            
            # AI Provider Tables
            self._create_ai_provider_tables(cursor)
            
            # Создание индексов для производительности
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_date ON messages(vk_chat_id, date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(message_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_stats_chat ON daily_stats(vk_chat_id)")
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def add_user(self, user_id: int, username: str = None, is_admin: bool = False):
        """Добавить пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, is_admin)
                VALUES (?, ?, ?)
            """, (user_id, username, is_admin))
            conn.commit()
    
    def add_group(self, group_id: int, group_name: str):
        """Добавить группу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO groups (group_id, group_name)
                VALUES (?, ?)
            """, (group_id, group_name))
            conn.commit()
    
    def add_group_user(self, group_id: int, user_id: int, is_admin: bool = False):
        """Добавить пользователя в группу"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO group_users (group_id, user_id, is_admin)
                VALUES (?, ?, ?)
            """, (group_id, user_id, is_admin))
            conn.commit()
    
    def get_user_groups(self, user_id: int) -> List[Dict]:
        """Получить группы пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.group_id, g.group_name, gu.is_admin
                FROM groups g
                JOIN group_users gu ON g.group_id = gu.group_id
                WHERE gu.user_id = ?
            """, (user_id,))
            return [{"group_id": row[0], "group_name": row[1], "is_admin": row[2]} for row in cursor.fetchall()]
    
    def get_all_groups(self) -> List[Dict]:
        """Получить все группы, где есть бот"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT group_id, group_name
                FROM groups
                ORDER BY group_name
            """)
            return [{"group_id": row[0], "group_name": row[1]} for row in cursor.fetchall()]
    
    def get_vk_chat_info(self, vk_chat_id: str) -> Optional[Dict]:
        """Получить информацию о VK чате"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chat_id, chat_name
                FROM vk_chats
                WHERE chat_id = ?
            """, (vk_chat_id,))
            result = cursor.fetchone()
            if result:
                return {
                    "chat_id": result[0],
                    "chat_name": result[1]
                }
            return None
    
    def add_vk_chat(self, chat_id: str, chat_name: str, chat_type: str = "chat"):
        """Добавить чат VK MAX"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO vk_chats (chat_id, chat_name, chat_type)
                VALUES (?, ?, ?)
            """, (chat_id, chat_name, chat_type))
            conn.commit()
    
    def add_group_vk_chat(self, group_id: int, vk_chat_id: str, added_by: int):
        """Связать группу с чатом VK MAX"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO group_vk_chats (group_id, vk_chat_id, added_by)
                VALUES (?, ?, ?)
            """, (group_id, vk_chat_id, added_by))
            conn.commit()
    
    def get_group_vk_chats(self, group_id: int) -> List[Dict]:
        """Получить чаты VK MAX для группы"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vc.chat_id, vc.chat_name, vc.chat_type
                FROM vk_chats vc
                JOIN group_vk_chats gvc ON vc.chat_id = gvc.vk_chat_id
                WHERE gvc.group_id = ?
            """, (group_id,))
            return [{"chat_id": row[0], "chat_name": row[1], "chat_type": row[2]} for row in cursor.fetchall()]
    
    def save_messages(self, vk_chat_id: str, messages: List[Dict]):
        """Сохранить сообщения в базу данных"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for message in messages:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO messages (
                            vk_chat_id, message_id, sender_id, sender_name, text,
                            message_time, date, message_type, attachments, reaction_info
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vk_chat_id,
                        message.get('message_id', ''),
                        message.get('sender_id'),
                        message.get('sender_name', ''),
                        message.get('text', ''),
                        message.get('message_time'),
                        message.get('date', ''),
                        message.get('message_type', 'USER'),
                        json.dumps(message.get('attachments', [])),
                        json.dumps(message.get('reaction_info', {}))
                    ))
                except Exception as e:
                    logger.error(f"Ошибка сохранения сообщения: {e}")
            
            conn.commit()
    
    def get_chat_stats(self, vk_chat_id: str) -> Dict:
        """Получить статистику чата"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общее количество сообщений
            cursor.execute("SELECT COUNT(*) FROM messages WHERE vk_chat_id = ?", (vk_chat_id,))
            total_messages = cursor.fetchone()[0]
            
            # Количество дней с сообщениями
            cursor.execute("SELECT COUNT(DISTINCT date) FROM messages WHERE vk_chat_id = ?", (vk_chat_id,))
            days_count = cursor.fetchone()[0]
            
            # Последние 5 дней
            cursor.execute("""
                SELECT date, COUNT(*) as message_count
                FROM messages 
                WHERE vk_chat_id = ?
                GROUP BY date
                ORDER BY date DESC
                LIMIT 5
            """, (vk_chat_id,))
            recent_days = [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            return {
                "total_messages": total_messages,
                "days_count": days_count,
                "recent_days": recent_days
            }
    
    def save_summary(self, vk_chat_id: str, date: str, summary_text: str, summary_type: str = "daily", 
                     reflection_text: str = None, improved_summary_text: str = None):
        """Сохранить суммаризацию"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO summaries (vk_chat_id, date, summary_text, summary_type, reflection_text, improved_summary_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vk_chat_id, date, summary_text, summary_type, reflection_text, improved_summary_text))
            conn.commit()
    
    def get_summary(self, vk_chat_id: str, date: str, summary_type: str = "daily") -> Optional[str]:
        """Получить суммаризацию"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT summary_text FROM summaries
                WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
            """, (vk_chat_id, date, summary_type))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_summary_with_reflection(self, vk_chat_id: str, date: str, summary_type: str = "daily") -> Dict[str, Optional[str]]:
        """Получить все типы суммаризации"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT summary_text, reflection_text, improved_summary_text FROM summaries
                WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
            """, (vk_chat_id, date, summary_type))
            result = cursor.fetchone()
            if result:
                return {
                    'summary': result[0],
                    'reflection': result[1],
                    'improved': result[2]
                }
            return {'summary': None, 'reflection': None, 'improved': None}
    
    def get_messages_by_date(self, vk_chat_id: str, date: str) -> List[Dict]:
        """Получить сообщения за определенную дату"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_id, sender_id, sender_name, text, message_time, 
                       message_type, attachments, reaction_info
                FROM messages 
                WHERE vk_chat_id = ? AND date = ?
                ORDER BY message_time ASC
            """, (vk_chat_id, date))
            
            messages = []
            for row in cursor.fetchall():
                message = {
                    "message_id": row[0],
                    "sender_id": row[1],
                    "sender_name": row[2],
                    "text": row[3],
                    "message_time": row[4],
                    "message_type": row[5],
                    "attachments": json.loads(row[6]) if row[6] else [],
                    "reaction_info": json.loads(row[7]) if row[7] else {}
                }
                messages.append(message)
            
            return messages
    
    def get_last_message_timestamp(self, vk_chat_id: str) -> Optional[int]:
        """Получить timestamp последнего сообщения в чате"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_time FROM messages 
                WHERE vk_chat_id = ? 
                ORDER BY message_time DESC 
                LIMIT 1
            """, (vk_chat_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_available_summaries(self, vk_chat_id: str) -> List[Dict]:
        """Получить список доступных суммаризаций для чата"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, summary_type, created_at
                FROM summaries 
                WHERE vk_chat_id = ?
                ORDER BY date DESC
            """, (vk_chat_id,))
            
            summaries = []
            for row in cursor.fetchall():
                summaries.append({
                    "date": row[0],
                    "summary_type": row[1],
                    "created_at": row[2]
                })
            
            return summaries
    
    def update_group_message(self, group_id: int, vk_chat_id: str, date: str, message_id: int):
        """Обновить сообщение в группе"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO group_messages (group_id, vk_chat_id, date, message_id)
                VALUES (?, ?, ?, ?)
            """, (group_id, vk_chat_id, date, message_id))
            conn.commit()
    
    def get_group_message(self, group_id: int, vk_chat_id: str, date: str) -> Optional[int]:
        """Получить message_id для обновления"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_id FROM group_messages
                WHERE group_id = ? AND vk_chat_id = ? AND date = ?
            """, (group_id, vk_chat_id, date))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def delete_group_message(self, group_id: int, vk_chat_id: str, date: str):
        """Удалить запись о сообщении в группе"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM group_messages
                WHERE group_id = ? AND vk_chat_id = ? AND date = ?
            """, (group_id, vk_chat_id, date))
            conn.commit()
    
    def _create_ai_provider_tables(self, cursor):
        """Создать таблицы для AI провайдеров"""
        # Пользовательские предпочтения AI провайдеров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_ai_preferences (
                user_id INTEGER PRIMARY KEY,
                default_provider TEXT DEFAULT 'gigachat',
                preferred_providers TEXT DEFAULT '["gigachat"]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Отслеживание доступности провайдеров
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provider_availability (
                provider_name TEXT PRIMARY KEY,
                is_available BOOLEAN DEFAULT TRUE,
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_count INTEGER DEFAULT 0,
                rate_limit_until TIMESTAMP NULL,
                last_error TEXT NULL
            )
        """)
        
        # Обновляем таблицу summaries для хранения информации о провайдере
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN provider_name TEXT DEFAULT 'gigachat'")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN provider_version TEXT")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        try:
            cursor.execute("ALTER TABLE summaries ADD COLUMN processing_time REAL")
        except sqlite3.OperationalError:
            pass  # Колонка уже существует
        
        # Пользовательские настройки моделей OpenRouter
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_openrouter_models (
                user_id INTEGER PRIMARY KEY,
                selected_model TEXT DEFAULT 'deepseek/deepseek-chat-v3.1:free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Создаем индексы для AI провайдеров
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_ai_preferences_user ON user_ai_preferences(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider_availability_name ON provider_availability(provider_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_summaries_provider ON summaries(provider_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_openrouter_models_user ON user_openrouter_models(user_id)")
    
    def add_user_ai_preference(self, user_id: int, default_provider: str = 'gigachat', preferred_providers: List[str] = None):
        """Добавить или обновить предпочтения AI провайдера пользователя"""
        if preferred_providers is None:
            preferred_providers = ['gigachat']
        
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_ai_preferences 
                (user_id, default_provider, preferred_providers, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, default_provider, json.dumps(preferred_providers)))
            conn.commit()
    
    def get_user_ai_preference(self, user_id: int) -> Optional[Dict]:
        """Получить предпочтения AI провайдера пользователя"""
        import json
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT default_provider, preferred_providers
                FROM user_ai_preferences
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if result:
                try:
                    preferred_providers = json.loads(result[1]) if result[1] else ['gigachat']
                except json.JSONDecodeError:
                    preferred_providers = ['gigachat']
                
                return {
                    'default_provider': result[0] or 'gigachat',
                    'preferred_providers': preferred_providers
                }
            return None
    
    def update_provider_availability(self, provider_name: str, is_available: bool, error_count: int = 0, last_error: str = None):
        """Обновить статус доступности провайдера"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO provider_availability 
                (provider_name, is_available, last_check, error_count, last_error)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (provider_name, is_available, error_count, last_error))
            conn.commit()
    
    def get_provider_availability(self, provider_name: str = None) -> Dict:
        """Получить статус доступности провайдеров"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if provider_name:
                cursor.execute("""
                    SELECT provider_name, is_available, last_check, error_count, last_error
                    FROM provider_availability
                    WHERE provider_name = ?
                """, (provider_name,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'provider_name': result[0],
                        'is_available': bool(result[1]),
                        'last_check': result[2],
                        'error_count': result[3],
                        'last_error': result[4]
                    }
                return {}
            else:
                cursor.execute("""
                    SELECT provider_name, is_available, last_check, error_count, last_error
                    FROM provider_availability
                    ORDER BY provider_name
                """)
                results = cursor.fetchall()
                
                availability = {}
                for row in results:
                    availability[row[0]] = {
                        'is_available': bool(row[1]),
                        'last_check': row[2],
                        'error_count': row[3],
                        'last_error': row[4]
                    }
                return availability
    
    def update_summary_with_provider_info(self, vk_chat_id: str, date: str, summary_type: str, 
                                        provider_name: str, provider_version: str = None, 
                                        processing_time: float = None):
        """Обновить суммаризацию с информацией о провайдере"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE summaries 
                SET provider_name = ?, provider_version = ?, processing_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
            """, (provider_name, provider_version, processing_time, vk_chat_id, date, summary_type))
            conn.commit()
    
    def get_summary_with_provider_info(self, vk_chat_id: str, date: str, summary_type: str = 'daily') -> Optional[Dict]:
        """Получить суммаризацию с информацией о провайдере"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, vk_chat_id, date, summary_text, summary_type, 
                       provider_name, provider_version, processing_time, created_at, updated_at
                FROM summaries
                WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
            """, (vk_chat_id, date, summary_type))
            result = cursor.fetchone()
            
            if result:
                return {
                    'id': result[0],
                    'vk_chat_id': result[1],
                    'date': result[2],
                    'summary_text': result[3],
                    'summary_type': result[4],
                    'provider_name': result[5] or 'gigachat',
                    'provider_version': result[6],
                    'processing_time': result[7],
                    'created_at': result[8],
                    'updated_at': result[9]
                }
            return None
    
    # OpenRouter Model Management
    def set_user_openrouter_model(self, user_id: int, model_id: str) -> bool:
        """Установить модель OpenRouter для пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_openrouter_models 
                (user_id, selected_model, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, model_id))
            conn.commit()
            return True
    
    def get_user_openrouter_model(self, user_id: int) -> str:
        """Получить выбранную модель OpenRouter для пользователя"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT selected_model FROM user_openrouter_models
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return 'deepseek/deepseek-chat-v3.1:free'  # Модель по умолчанию
