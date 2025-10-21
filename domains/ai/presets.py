"""
Реестр готовых пресетов для анализа
"""
from pydantic import BaseModel
from typing import List
from .models import StepType

class AnalysisPreset(BaseModel):
    """Готовый пресет анализа"""
    id: str
    name: str
    description: str
    steps: List[StepType]
    icon: str = "⚡"

class PresetRegistry:
    """Реестр готовых пресетов"""
    
    PRESETS = {
        "fast": AnalysisPreset(
            id="fast",
            name="Быстрая суммаризация",
            description="Быстрый анализ без дополнительных шагов",
            steps=[StepType.SUMMARIZATION],
            icon="⚡"
        ),
        "reflection": AnalysisPreset(
            id="reflection",
            name="С рефлексией",
            description="Суммаризация + критический анализ + улучшенная версия",
            steps=[StepType.SUMMARIZATION, StepType.REFLECTION, StepType.IMPROVEMENT],
            icon="🔄"
        ),
        "cleaning": AnalysisPreset(
            id="cleaning",
            name="С очисткой данных",
            description="Фильтрация важных сообщений + суммаризация",
            steps=[StepType.CLEANING, StepType.SUMMARIZATION],
            icon="🧹"
        ),
        "structured": AnalysisPreset(
            id="structured",
            name="Структурированный анализ",
            description="Классификация + экстракция + сводка для родителей",
            steps=[StepType.CLASSIFICATION, StepType.EXTRACTION, StepType.PARENT_SUMMARY],
            icon="🔍"
        ),
        "with_schedule": AnalysisPreset(
            id="with_schedule",
            name="С анализом расписания",
            description="Суммаризация + анализ расписания на завтра",
            steps=[StepType.SUMMARIZATION, StepType.SCHEDULE_ANALYSIS],
            icon="📅"
        ),
        "full": AnalysisPreset(
            id="full",
            name="Полный анализ",
            description="Все шаги: очистка + суммаризация + рефлексия + улучшение + расписание",
            steps=[StepType.CLEANING, StepType.SUMMARIZATION, StepType.REFLECTION, StepType.IMPROVEMENT, StepType.SCHEDULE_ANALYSIS],
            icon="🎯"
        )
    }
    
    @classmethod
    def get_preset(cls, preset_id: str) -> AnalysisPreset:
        """Получить пресет по ID"""
        return cls.PRESETS.get(preset_id)
    
    @classmethod
    def get_all_presets(cls) -> List[AnalysisPreset]:
        """Получить все пресеты"""
        return list(cls.PRESETS.values())
    
    @classmethod
    def get_preset_ids(cls) -> List[str]:
        """Получить список ID всех пресетов"""
        return list(cls.PRESETS.keys())

