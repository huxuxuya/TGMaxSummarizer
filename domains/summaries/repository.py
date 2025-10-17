from typing import List, Dict, Any, Optional
from core.database.base_repository import BaseRepository
from .models import Summary, SummaryType, SummaryInfo

class SummaryRepository(BaseRepository):
    """Репозиторий для работы с суммаризациями"""
    
    def _table_name(self) -> str:
        return "summaries"
    
    def _create_table_sql(self) -> str:
        return """
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_chat_id TEXT,
                date TEXT,
                summary_text TEXT,
                reflection_text TEXT,
                improved_summary_text TEXT,
                summary_type TEXT DEFAULT 'daily',
                provider_name TEXT DEFAULT 'gigachat',
                provider_version TEXT,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model_provider TEXT,
                model_id TEXT,
                scenario_type TEXT,
                generation_time_seconds REAL,
                UNIQUE(vk_chat_id, date, summary_type)
            )
        """
    
    def save_summary(self, summary: Summary) -> bool:
        """Сохранить суммаризацию"""
        query = """
            INSERT OR REPLACE INTO summaries (
                vk_chat_id, date, summary_text, summary_type, 
                reflection_text, improved_summary_text, provider_name, 
                provider_version, processing_time, model_provider, 
                model_id, scenario_type, generation_time_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Handle both enum and string types for summary_type
        summary_type_value = summary.summary_type.value if hasattr(summary.summary_type, 'value') else str(summary.summary_type)
        
        affected = self.execute_update(query, (
            summary.vk_chat_id,
            summary.date,
            summary.summary_text,
            summary_type_value,
            summary.reflection_text,
            summary.improved_summary_text,
            summary.provider_name,
            summary.provider_version,
            summary.processing_time,
            summary.model_provider,
            summary.model_id,
            summary.scenario_type,
            summary.generation_time_seconds
        ))
        return affected > 0
    
    def get_summary(self, vk_chat_id: str, date: str, summary_type: SummaryType = SummaryType.DAILY) -> Optional[Summary]:
        """Получить суммаризацию"""
        query = """
            SELECT id, vk_chat_id, date, summary_text, summary_type,
                   reflection_text, improved_summary_text, provider_name,
                   provider_version, processing_time, created_at, updated_at,
                   model_provider, model_id, scenario_type, generation_time_seconds
            FROM summaries
            WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
        """
        # Handle both enum and string types for summary_type
        summary_type_value = summary_type.value if hasattr(summary_type, 'value') else str(summary_type)
        results = self.execute_query(query, (vk_chat_id, date, summary_type_value))
        if results:
            row = results[0]
            return Summary(
                id=row['id'],
                vk_chat_id=row['vk_chat_id'],
                date=row['date'],
                summary_text=row['summary_text'],
                summary_type=SummaryType(row['summary_type']),
                reflection_text=row['reflection_text'],
                improved_summary_text=row['improved_summary_text'],
                provider_name=row['provider_name'] or 'gigachat',
                provider_version=row['provider_version'],
                processing_time=row['processing_time'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                model_provider=row['model_provider'],
                model_id=row['model_id'],
                scenario_type=row['scenario_type'],
                generation_time_seconds=row['generation_time_seconds']
            )
        return None
    
    def get_summary_with_reflection(self, vk_chat_id: str, date: str, summary_type: SummaryType = SummaryType.DAILY) -> Dict[str, Optional[str]]:
        """Получить все типы суммаризации"""
        query = """
            SELECT summary_text, reflection_text, improved_summary_text 
            FROM summaries
            WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
        """
        # Handle both enum and string types for summary_type
        summary_type_value = summary_type.value if hasattr(summary_type, 'value') else str(summary_type)
        results = self.execute_query(query, (vk_chat_id, date, summary_type_value))
        if results:
            row = results[0]
            return {
                'summary': row['summary_text'],
                'reflection': row['reflection_text'],
                'improved': row['improved_summary_text']
            }
        return {'summary': None, 'reflection': None, 'improved': None}
    
    def get_available_summaries(self, vk_chat_id: str) -> List[SummaryInfo]:
        """Получить список доступных суммаризаций для чата"""
        query = """
            SELECT s.date, s.summary_type, s.created_at, COUNT(m.message_id) as count
            FROM summaries s
            LEFT JOIN messages m ON s.vk_chat_id = m.vk_chat_id AND s.date = m.date
            WHERE s.vk_chat_id = ?
            GROUP BY s.date, s.summary_type, s.created_at
            ORDER BY s.date DESC
        """
        results = self.execute_query(query, (vk_chat_id,))
        return [SummaryInfo(**row) for row in results]
    
    def update_summary_with_provider_info(self, vk_chat_id: str, date: str, summary_type: SummaryType,
                                        provider_name: str, provider_version: str = None, 
                                        processing_time: float = None) -> bool:
        """Обновить суммаризацию с информацией о провайдере"""
        query = """
            UPDATE summaries 
            SET provider_name = ?, provider_version = ?, processing_time = ?, updated_at = CURRENT_TIMESTAMP
            WHERE vk_chat_id = ? AND date = ? AND summary_type = ?
        """
        # Handle both enum and string types for summary_type
        summary_type_value = summary_type.value if hasattr(summary_type, 'value') else str(summary_type)
        
        affected = self.execute_update(query, (
            provider_name, provider_version, processing_time, 
            vk_chat_id, date, summary_type_value
        ))
        return affected > 0

