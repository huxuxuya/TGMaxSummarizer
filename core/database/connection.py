import sqlite3
import logging
from typing import Optional
from pathlib import Path
from ..exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Менеджер соединений с базой данных"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """Создать директорию для БД если не существует"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить соединение с базой данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise DatabaseError(f"Не удалось подключиться к БД: {e}")
    
    def execute_with_connection(self, operation, *args, **kwargs):
        """Выполнить операцию с автоматическим управлением соединением"""
        with self.get_connection() as conn:
            return operation(conn, *args, **kwargs)

