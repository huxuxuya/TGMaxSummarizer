from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from .connection import DatabaseConnection
from ..exceptions import DatabaseError
import logging

T = TypeVar('T')

logger = logging.getLogger(__name__)

class BaseRepository(ABC, Generic[T]):
    """Базовый репозиторий для работы с БД"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    @abstractmethod
    def _table_name(self) -> str:
        """Имя таблицы для данного репозитория"""
        pass
    
    @abstractmethod
    def _create_table_sql(self) -> str:
        """SQL для создания таблицы"""
        pass
    
    def create_table(self):
        """Создать таблицу если не существует"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(self._create_table_sql())
                conn.commit()
                logger.debug(f"Таблица {self._table_name()} создана/проверена")
        except Exception as e:
            logger.error(f"Ошибка создания таблицы {self._table_name()}: {e}")
            raise DatabaseError(f"Не удалось создать таблицу {self._table_name()}: {e}")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполнить SELECT запрос"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            raise DatabaseError(f"Ошибка выполнения запроса: {e}")
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Выполнить INSERT/UPDATE/DELETE запрос"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Ошибка выполнения обновления: {e}")
            raise DatabaseError(f"Ошибка выполнения обновления: {e}")
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Выполнить запрос для множества параметров"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Ошибка выполнения batch запроса: {e}")
            raise DatabaseError(f"Ошибка выполнения batch запроса: {e}")
    
    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """Получить запись по ID"""
        query = f"SELECT * FROM {self._table_name()} WHERE id = ?"
        results = self.execute_query(query, (id_value,))
        return results[0] if results else None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Получить все записи"""
        query = f"SELECT * FROM {self._table_name()}"
        return self.execute_query(query)
    
    def delete_by_id(self, id_value: Any) -> bool:
        """Удалить запись по ID"""
        query = f"DELETE FROM {self._table_name()} WHERE id = ?"
        affected = self.execute_update(query, (id_value,))
        return affected > 0

