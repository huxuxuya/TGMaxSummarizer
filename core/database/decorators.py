from functools import wraps
import logging

logger = logging.getLogger(__name__)

def transactional(func):
    """Decorator для выполнения метода в транзакции"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Get database connection from any repository
        db_connection = None
        if hasattr(self, 'db'):
            db_connection = self.db
        elif hasattr(self, 'chat_repo'):
            db_connection = self.chat_repo.db
        elif hasattr(self, 'message_repo'):
            db_connection = self.message_repo.db
        elif hasattr(self, 'group_repo'):
            db_connection = self.group_repo.db
        else:
            raise AttributeError("No database connection found in object")
        
        with db_connection.get_connection() as conn:
            try:
                # Start transaction
                conn.execute("BEGIN TRANSACTION")
                
                # Execute function
                result = func(self, *args, **kwargs)
                
                # Commit
                conn.commit()
                return result
                
            except Exception as e:
                # Rollback on error
                conn.rollback()
                logger.error(f"Transaction failed in {func.__name__}: {e}")
                raise
    
    return wrapper
