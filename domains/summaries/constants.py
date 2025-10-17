class SummarizationScenarios:
    """Константы для сценариев суммаризации"""
    
    FAST = "fast"
    REFLECTION = "reflection"
    CLEANING = "cleaning"
    STRUCTURED = "structured"
    
    ALL = [FAST, REFLECTION, CLEANING, STRUCTURED]
    
    NAMES = {
        FAST: "⚡ Быстрая",
        REFLECTION: "🔄 С рефлексией",
        CLEANING: "🧹 С очисткой",
        STRUCTURED: "🔍 Структурированная"
    }
    
    @classmethod
    def get_display_name(cls, scenario: str) -> str:
        """Получить отображаемое название сценария"""
        return cls.NAMES.get(scenario, scenario)
    
    @classmethod
    def is_valid(cls, scenario: str) -> bool:
        """Проверить, является ли сценарий валидным"""
        return scenario in cls.ALL
