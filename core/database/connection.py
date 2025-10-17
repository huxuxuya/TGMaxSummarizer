import sqlite3
import logging
import threading
from typing import Optional
from pathlib import Path
from contextlib import contextmanager
from ..exceptions import DatabaseError

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Менеджер соединений с базой данных с пулом соединений"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = []
        self._lock = threading.Lock()
        self._ensure_db_directory()
        self._initialize_pool()
    
    def _ensure_db_directory(self):
        """Создать директорию для БД если не существует"""
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_pool(self):
        """Инициализировать пул соединений"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.append(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Создать новое соединение с оптимизированными настройками"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Ошибка создания соединения с БД: {e}")
            raise DatabaseError(f"Не удалось создать соединение с БД: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager для получения соединения из пула"""
        conn = None
        try:
            with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                else:
                    conn = self._create_connection()
            
            yield conn
            
        finally:
            if conn:
                with self._lock:
                    if len(self._pool) < self.pool_size:
                        self._pool.append(conn)
                    else:
                        conn.close()
    
    def close_all(self):
        """Закрыть все соединения в пуле"""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()
    
    def execute_with_connection(self, operation, *args, **kwargs):
        """Выполнить операцию с автоматическим управлением соединением"""
        with self.get_connection() as conn:
            return operation(conn, *args, **kwargs)

