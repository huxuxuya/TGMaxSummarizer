from typing import List, Dict, Any, Optional
from .models import Summary, SummaryType, SummaryResult, SummaryInfo
from .repository import SummaryRepository
from core.database.connection import DatabaseConnection
from core.exceptions import ValidationError

class SummaryService:
    """Сервис для работы с суммаризациями"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.summary_repo = SummaryRepository(db_connection)
        self.summary_repo.create_table()
    
    def save_summary(self, summary: Summary) -> bool:
        """Сохранить суммаризацию"""
        return self.summary_repo.save_summary(summary)
    
    def get_summary(self, vk_chat_id: str, date: str, summary_type: SummaryType = SummaryType.DAILY) -> Optional[Summary]:
        """Получить суммаризацию"""
        return self.summary_repo.get_summary(vk_chat_id, date, summary_type)
    
    def get_summary_with_reflection(self, vk_chat_id: str, date: str, summary_type: SummaryType = SummaryType.DAILY) -> Dict[str, Optional[str]]:
        """Получить все типы суммаризации"""
        return self.summary_repo.get_summary_with_reflection(vk_chat_id, date, summary_type)
    
    def get_available_summaries(self, vk_chat_id: str) -> List[SummaryInfo]:
        """Получить список доступных суммаризаций"""
        return self.summary_repo.get_available_summaries(vk_chat_id)
    
    def update_summary_with_provider_info(self, vk_chat_id: str, date: str, summary_type: SummaryType,
                                        provider_name: str, provider_version: str = None, 
                                        processing_time: float = None) -> bool:
        """Обновить суммаризацию с информацией о провайдере"""
        return self.summary_repo.update_summary_with_provider_info(
            vk_chat_id, date, summary_type, provider_name, provider_version, processing_time
        )
    
    def save_summary_result(self, vk_chat_id: str, date: str, result: SummaryResult, 
                          provider_name: str, summary_type: SummaryType = SummaryType.DAILY) -> bool:
        """Сохранить результат анализа с рефлексией"""
        summary = Summary(
            vk_chat_id=vk_chat_id,
            date=date,
            summary_text=result.summary,
            reflection_text=result.reflection,
            improved_summary_text=result.improved,
            summary_type=summary_type,
            provider_name=provider_name
        )
        return self.save_summary(summary)

