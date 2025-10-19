from typing import List, Dict, Any, Optional
import json
from .models import Summary, SummaryType, SummaryResult, SummaryInfo
from .repository import SummaryRepository
from core.database.connection import DatabaseConnection
from core.exceptions import ValidationError

class SummaryService:
    """Сервис для работы с суммаризациями"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.summary_repo = SummaryRepository(db_connection)
        self.summary_repo.create_table()
        self.summary_repo._migrate_add_structured_fields()
    
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
    
    def extract_step_results_from_analysis(
        self, 
        result, 
        scenario_type: str
    ) -> Dict[str, Optional[str]]:
        """
        Извлечь структурированные данные из результата анализа
        
        Args:
            result: AnalysisResult с метаданными
            scenario_type: Тип сценария (fast, reflection, cleaning, structured)
            
        Returns:
            Dict с полями: summary, reflection, improved, 
            classification, extraction, parent_summary
        """
        step_data = {
            'summary': None,
            'reflection': None,
            'improved': None,
            'classification': None,
            'extraction': None,
            'parent_summary': None
        }
        
        # Проверяем наличие step_results в metadata
        if not hasattr(result, 'metadata') or not result.metadata:
            return step_data
            
        step_results = result.metadata.get('step_results', {})
        if not step_results:
            return step_data
        
        # Извлекаем данные для соответствующих шагов
        if 'summarization' in step_results:
            step_data['summary'] = step_results['summarization']
            
        if 'reflection' in step_results:
            step_data['reflection'] = step_results['reflection']
            
        if 'improvement' in step_results:
            step_data['improved'] = step_results['improvement']
            
        if 'classification' in step_results:
            classification_data = step_results['classification']
            if classification_data:
                try:
                    # Конвертируем в JSON если это не строка
                    if isinstance(classification_data, (list, dict)):
                        step_data['classification'] = json.dumps(classification_data, ensure_ascii=False)
                    else:
                        step_data['classification'] = str(classification_data)
                except (TypeError, ValueError) as e:
                    print(f"⚠️ Ошибка сериализации classification: {e}")
                    step_data['classification'] = str(classification_data)
                    
        if 'extraction' in step_results:
            extraction_data = step_results['extraction']
            if extraction_data:
                try:
                    # Конвертируем в JSON если это не строка
                    if isinstance(extraction_data, (list, dict)):
                        step_data['extraction'] = json.dumps(extraction_data, ensure_ascii=False)
                    else:
                        step_data['extraction'] = str(extraction_data)
                except (TypeError, ValueError) as e:
                    print(f"⚠️ Ошибка сериализации extraction: {e}")
                    step_data['extraction'] = str(extraction_data)
                    
        if 'parent_summary' in step_results:
            step_data['parent_summary'] = step_results['parent_summary']
        
        return step_data

