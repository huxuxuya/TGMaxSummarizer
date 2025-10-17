from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

class UserState(BaseModel):
    """Состояние пользователя"""
    user_id: int
    current_step: str
    data: Dict[str, Any]
    expires_at: datetime
    created_at: datetime = datetime.now()

class StateManager:
    """Manager для состояний пользователей с персистентностью"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._create_table()
    
    def _create_table(self):
        """Создать таблицу состояний"""
        query = """
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                current_step TEXT,
                data TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        with self.db.get_connection() as conn:
            conn.execute(query)
            conn.commit()
    
    def get_state(self, user_id: int) -> Optional[UserState]:
        """Получить состояние пользователя"""
        query = """
            SELECT * FROM user_states 
            WHERE user_id = ? AND expires_at > datetime('now')
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            
            if row:
                return UserState(
                    user_id=row['user_id'],
                    current_step=row['current_step'],
                    data=json.loads(row['data']),
                    expires_at=datetime.fromisoformat(row['expires_at']),
                    created_at=datetime.fromisoformat(row['created_at'])
                )
            return None
    
    def set_state(self, user_id: int, step: str, data: Dict[str, Any], 
                  ttl_minutes: int = 30):
        """Установить состояние пользователя"""
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        query = """
            INSERT OR REPLACE INTO user_states 
            (user_id, current_step, data, expires_at)
            VALUES (?, ?, ?, ?)
        """
        with self.db.get_connection() as conn:
            conn.execute(query, (user_id, step, json.dumps(data), expires_at))
            conn.commit()
    
    def clear_state(self, user_id: int):
        """Очистить состояние пользователя"""
        query = "DELETE FROM user_states WHERE user_id = ?"
        with self.db.get_connection() as conn:
            conn.execute(query, (user_id,))
            conn.commit()
