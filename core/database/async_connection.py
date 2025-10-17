import asyncio
from typing import List, Dict, Any, Optional
from .connection import DatabaseConnection
from ..exceptions import DatabaseError
import logging

logger = logging.getLogger(__name__)

class AsyncDatabaseConnection:
    """Async wrapper для DatabaseConnection"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self._db = db_connection
    
    async def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполнить SELECT запрос асинхронно"""
        def _execute():
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        return await asyncio.to_thread(_execute)
    
    async def execute_update(self, query: str, params: tuple = ()) -> int:
        """Выполнить INSERT/UPDATE/DELETE запрос асинхронно"""
        def _execute():
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
        
        return await asyncio.to_thread(_execute)
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Выполнить batch запрос асинхронно"""
        def _execute():
            with self._db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
        
        return await asyncio.to_thread(_execute)
    
    async def execute_transaction(self, operations: List[tuple]) -> bool:
        """Выполнить несколько операций в одной транзакции"""
        def _execute():
            with self._db.get_connection() as conn:
                try:
                    cursor = conn.cursor()
                    for query, params in operations:
                        cursor.execute(query, params)
                    conn.commit()
                    return True
                except Exception as e:
                    conn.rollback()
                    raise DatabaseError(f"Transaction failed: {e}")
        
        return await asyncio.to_thread(_execute)
