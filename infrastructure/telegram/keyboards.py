"""
Клавиатуры для Telegram бота
"""
import json
import os
from typing import List, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from shared.utils import shorten_callback_data

def main_menu_keyboard(chats_count: int = 0, chats: list = None):
    """Главное меню (упрощенное)"""
    keyboard = []
    
    # Если чатов мало - показываем сразу
    if chats and len(chats) <= 3:
        for chat in chats:
            # Support both Pydantic models and dicts
            if hasattr(chat, 'chat_id'):
                chat_id = chat.chat_id
                chat_name = chat.chat_name
            else:
                chat_id = chat['chat_id']
                chat_name = chat.get('chat_name', f'Чат {chat_id}')
            
            keyboard.append([InlineKeyboardButton(
                f"💬 {chat_name}", 
                callback_data=f"quick_chat_{chat_id}"
            )])
    else:
        keyboard.append([InlineKeyboardButton(
            "📊 Выбрать чат", 
            callback_data="select_chat_quick"
        )])
    
    # Быстрые действия (без выбора чата)
    keyboard.append([InlineKeyboardButton("⚡ Быстрые действия", callback_data="quick_actions")])
    
    # AI, Расписание, Управление чатами и Настройки
    keyboard.extend([
        [InlineKeyboardButton("🤖 AI Модели", callback_data="select_ai_provider")],
        [InlineKeyboardButton("📅 Управление расписанием", callback_data="schedule_management")],
        [InlineKeyboardButton("📊 Управление чатами", callback_data="manage_chats")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings_menu")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def group_selection_keyboard(groups: list):
    """Клавиатура выбора группы"""
    keyboard = []
    for group in groups:
        # Support both Pydantic models and dicts
        if hasattr(group, 'group_id'):
            group_id = group.group_id
            group_name = group.group_name
        else:
            group_id = group['group_id']
            group_name = group['group_name']
        
        keyboard.append([InlineKeyboardButton(
            f"📱 {group_name}", 
            callback_data=f"select_group_{group_id}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def group_selection_for_schedule_keyboard(groups: list):
    """Клавиатура выбора группы для управления расписанием"""
    keyboard = []
    for group in groups:
        # Support both Pydantic models and dicts
        if hasattr(group, 'group_id'):
            group_id = group.group_id
            group_name = group.group_name
        else:
            group_id = group['group_id']
            group_name = group['group_name']
        
        keyboard.append([InlineKeyboardButton(
            f"📱 {group_name}", 
            callback_data=f"select_group_for_schedule_{group_id}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def chat_management_keyboard(group_id: int = None):
    """Клавиатура управления чатами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("❌ Удалить чат", callback_data="remove_chat")],
        [InlineKeyboardButton("📋 Список чатов", callback_data="list_chats")],
        [InlineKeyboardButton("⚙️ Настройки чата", callback_data="chat_settings")]
    ]
    
    # Определяем куда ведет кнопка "Назад" в зависимости от контекста
    if group_id:
        # Если мы в контексте конкретной группы, возвращаемся к меню группы
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"back_to_group_{group_id}")])
    else:
        # Если это общее меню управления чатами, возвращаемся в главное меню
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def group_chat_management_keyboard(group_id: int):
    """Клавиатура управления чатами конкретной группы"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("❌ Удалить чат", callback_data="remove_chat")],
        [InlineKeyboardButton("📋 Список чатов", callback_data="list_chats")],
        [InlineKeyboardButton("⚙️ Настройки чата", callback_data="chat_settings")],
        [InlineKeyboardButton("🔙 Назад к группе", callback_data=f"back_to_group_{group_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def chat_list_keyboard(chats: list, has_schedule: bool = False, context: str = "select"):
    """
    Клавиатура списка чатов
    context: "select" (для select_chat_) или "quick" (для quick_chat_)
    """
    keyboard = []
    for chat in chats:
        # Используем разные callback_data в зависимости от контекста
        if context == "quick":
            callback_data = f"quick_chat_{chat['chat_id']}"
        else:
            callback_data = f"select_chat_{chat['chat_id']}"
            
        keyboard.append([InlineKeyboardButton(
            f"💬 {chat['chat_name']}", 
            callback_data=callback_data
        )])
    
    # Добавляем кнопку добавления чата
    keyboard.append([InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")])
    
    # Добавляем кнопку расписания
    if has_schedule:
        keyboard.append([InlineKeyboardButton("🗑️ Удалить расписание", callback_data="delete_schedule")])
    else:
        keyboard.append([InlineKeyboardButton("📅 Установить расписание", callback_data="set_schedule")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])  # ИСПРАВЛЕНО
    return InlineKeyboardMarkup(keyboard)

def chat_settings_keyboard(vk_chat_id: str):
    """Клавиатура настроек чата"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data=f"chat_stats_{vk_chat_id}")],
        [InlineKeyboardButton("🔄 Загрузить сообщения", callback_data=f"load_messages_{vk_chat_id}")],
        [InlineKeyboardButton("📋 Проверить суммаризацию", callback_data=f"check_summary_{vk_chat_id}")],
        [InlineKeyboardButton("📤 Вывести в группу", callback_data=f"publish_menu_{vk_chat_id}")],  # ИЗМЕНЕНО
        [InlineKeyboardButton("🔙 Назад", callback_data=f"quick_chat_{vk_chat_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    """Кнопка 'Назад'"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)

def cancel_keyboard():
    """Кнопка 'Отмена'"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(action: str, data: str = ""):
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Нет", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def date_selection_keyboard(dates: list, vk_chat_id: str = None):
    """Клавиатура выбора даты"""
    keyboard = []
    for date in dates:
        # Handle both dict and model objects
        if hasattr(date, 'date'):
            date_str = date.date
            count = date.count
        else:
            date_str = date['date']
            count = date['count']
            
        keyboard.append([InlineKeyboardButton(
            f"📅 {date_str} ({count} сообщений)", 
            callback_data=f"select_date_{date_str}"
        )])
    keyboard.append([InlineKeyboardButton("🤖 Выбрать модель для анализа", callback_data="select_model_for_analysis")])
    # ИСПРАВЛЕНО: правильная кнопка назад
    if vk_chat_id:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"quick_chat_{vk_chat_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def available_chats_keyboard(chats: list, page: int = 0, per_page: int = 10, context: str = "select"):
    """
    Клавиатура выбора доступных чатов VK MAX
    context: "select" (для select_chat_) или "quick" (для quick_chat_)
    """
    keyboard = []
    
    # Вычисляем диапазон для текущей страницы
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_chats = chats[start_idx:end_idx]
    
    for chat in page_chats:
        # Ограничиваем длину названия чата
        title = chat['title'][:30] + "..." if len(chat['title']) > 30 else chat['title']
        participants = chat['participants_count']
        
        button_text = f"💬 {title} ({participants} чел.)"
        
        # Используем разные callback_data в зависимости от контекста
        if context == "quick":
            callback_data = f"quick_chat_{chat['id']}"
        else:
            callback_data = f"select_available_chat_{chat['id']}"
            
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=callback_data
        )])
    
    # Добавляем навигацию по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton("⬅️ Предыдущая", callback_data=f"chats_page_{page-1}"))
    
    if end_idx < len(chats):
        navigation_buttons.append(InlineKeyboardButton("Следующая ➡️", callback_data=f"chats_page_{page+1}"))
    
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    # Добавляем кнопки управления
    keyboard.append([InlineKeyboardButton("🔍 Поиск по ID", callback_data="search_chat_by_id")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])  # ИСПРАВЛЕНО
    
    return InlineKeyboardMarkup(keyboard)

def chat_add_method_keyboard():
    """Клавиатура выбора способа добавления чата"""
    keyboard = [
        [InlineKeyboardButton("📋 Выбрать из списка", callback_data="select_from_list")],
        [InlineKeyboardButton("🔍 Ввести ID вручную", callback_data="enter_chat_id")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_manage_chats")]
    ]
    return InlineKeyboardMarkup(keyboard)

# AI Provider Keyboards
def ai_provider_selection_keyboard(available_providers: List[str], current_provider: str = None, provider_info: List[Dict] = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора AI провайдера"""
    buttons = []
    
    # Маппинг имен провайдеров для отображения
    provider_display_names = {
        'gigachat': '🤖 GigaChat',
        'chatgpt': '🧠 ChatGPT',
        'openrouter': '🔗 OpenRouter',
        'gemini': '💎 Gemini',
        'ollama': '🦙 Ollama'
    }
    
    # Создаем словарь статусов провайдеров
    provider_status = {}
    if provider_info:
        for info in provider_info:
            # info может быть как словарем, так и объектом ProviderInfo
            if hasattr(info, 'name'):
                # Это объект ProviderInfo
                provider_status[info.name] = info.available
            else:
                # Это словарь
                provider_status[info['name']] = info.get('available', False)
    
    for provider in available_providers:
        display_name = provider_display_names.get(provider, f"⚙️ {provider.title()}")
        
        # Определяем префикс в зависимости от статуса и текущего выбора
        if provider == current_provider:
            prefix = "✅ "
        elif provider_status.get(provider, False):
            prefix = "⚪ "
        else:
            prefix = "❌ "
        
        buttons.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"select_provider:{provider}"
        )])
    
    # Добавляем кнопку "Топ-5 моделей" если OpenRouter доступен
    if 'openrouter' in available_providers and provider_status.get('openrouter', False):
        buttons.append([InlineKeyboardButton("🏆 Топ-5 моделей", callback_data="top5_models_selection")])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(buttons)

def ai_provider_settings_keyboard(user_preferences: Dict = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру для настроек AI провайдера"""
    buttons = [
        [InlineKeyboardButton("🎯 Выбрать модель", callback_data="select_ai_provider")],
        [InlineKeyboardButton("⚙️ Настройки по умолчанию", callback_data="ai_provider_defaults")],
        [InlineKeyboardButton("📋 Сценарий суммаризации", callback_data="scenario_defaults")],
        [InlineKeyboardButton("🗑️ Очистить настройки", callback_data="clear_ai_settings")],
        [InlineKeyboardButton("📊 Статус провайдеров", callback_data="ai_provider_status")],
        [InlineKeyboardButton("🔍 Проверить доступность", callback_data="check_providers_availability")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def ai_provider_defaults_keyboard(current_default: str = 'gigachat') -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора провайдера по умолчанию"""
    buttons = []
    
    provider_display_names = {
        'gigachat': '🤖 GigaChat',
        'chatgpt': '🧠 ChatGPT', 
        'openrouter': '🔗 OpenRouter',
        'gemini': '💎 Gemini',
        'ollama': '🦙 Ollama'
    }
    
    for provider, display_name in provider_display_names.items():
        prefix = "✅ " if provider == current_default else "⚪ "
        buttons.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"set_default_provider:{provider}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")])
    return InlineKeyboardMarkup(buttons)

def scenario_defaults_keyboard(current_default: str = 'fast') -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора сценария суммаризации по умолчанию"""
    buttons = []
    
    scenario_display_names = {
        'fast': '⚡ Быстрая',
        'reflection': '🔄 С рефлексией',
        'cleaning': '🧹 С очисткой',
        'structured': '🔍 Структурированная'
    }
    
    for scenario, display_name in scenario_display_names.items():
        prefix = "✅ " if scenario == current_default else "⚪ "
        buttons.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"set_default_scenario:{scenario}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")])
    return InlineKeyboardMarkup(buttons)

def confirm_ai_provider_change_keyboard(provider_name: str) -> InlineKeyboardMarkup:
    """Создать клавиатуру подтверждения смены провайдера"""
    provider_display_names = {
        'gigachat': 'GigaChat',
        'chatgpt': 'ChatGPT',
        'openrouter': 'OpenRouter', 
        'gemini': 'Gemini',
        'ollama': 'Ollama'
    }
    
    display_name = provider_display_names.get(provider_name, provider_name.title())
    
    buttons = [
        [InlineKeyboardButton(f"✅ Да, использовать {display_name}", callback_data=f"confirm_provider:{provider_name}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="select_ai_provider")],
        [InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")]
    ]
    return InlineKeyboardMarkup(buttons)

# OpenRouter Model Selection Keyboards
def openrouter_model_selection_keyboard(available_models: Dict[str, Dict], current_model: str = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора модели OpenRouter"""
    buttons = []
    
    for model_id, model_info in available_models.items():
        display_name = model_info.get('display_name', model_id)
        free_indicator = "🆓" if model_info.get('free', False) else "💰"
        prefix = "✅ " if model_id == current_model else "⚪ "
        
        # Ограничиваем длину названия для кнопки
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        
        buttons.append([InlineKeyboardButton(
            f"{prefix}{free_indicator} {display_name}",
            callback_data=shorten_callback_data(f"select_openrouter_model:{model_id}")
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="select_ai_provider")])
    return InlineKeyboardMarkup(buttons)

def openrouter_model_info_keyboard(model_id: str) -> InlineKeyboardMarkup:
    """Создать клавиатуру с информацией о модели OpenRouter"""
    buttons = [
        [InlineKeyboardButton("✅ Выбрать эту модель", callback_data=f"confirm_openrouter_model:{model_id}")],
        [InlineKeyboardButton("🔙 Назад к моделям", callback_data="openrouter_model_selection")],
        [InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="select_ai_provider")]
    ]
    return InlineKeyboardMarkup(buttons)

def top5_models_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру с топ-5 лучшими моделями"""
    try:
        # Загружаем конфигурацию топ-5 моделей
        config_path = os.path.join(os.path.dirname(__file__), 'top5_models_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            top5_models = config.get('top5_models', [])
        else:
            # Fallback конфигурация
            top5_models = [
                {
                    "id": "nvidia/nemotron-nano-9b-v2:free",
                    "name": "NVIDIA Nemotron Nano 9B v2",
                    "description": "🚀 Быстрая и надежная модель NVIDIA"
                },
                {
                    "id": "deepseek/deepseek-chat-v3.1:free",
                    "name": "DeepSeek V3.1", 
                    "description": "🧠 Мощная модель с reasoning"
                },
                {
                    "id": "qwen/qwen3-235b-a22b:free",
                    "name": "Qwen3 235B A22B",
                    "description": "💎 Самая мощная бесплатная модель"
                },
                {
                    "id": "mistralai/mistral-small-3.2-24b-instruct:free",
                    "name": "Mistral Small 3.2 24B",
                    "description": "⚡ Быстрая модель Mistral"
                },
                {
                    "id": "meta-llama/llama-3.3-8b-instruct:free",
                    "name": "Meta Llama 3.3 8B",
                    "description": "🦙 Надежная модель от Meta"
                }
            ]
        
        buttons = []
        for i, model in enumerate(top5_models, 1):
            # Создаем кнопку для каждой модели
            button_text = f"{i}. {model['name']}"
            callback_data = shorten_callback_data(f"select_top5_model:{model['id']}")
            buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Добавляем кнопки навигации
        buttons.append([InlineKeyboardButton("📋 Все модели OpenRouter", callback_data="openrouter_model_selection")])
        buttons.append([InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="select_ai_provider")])
        
        return InlineKeyboardMarkup(buttons)
        
    except Exception as e:
        # В случае ошибки возвращаем простую клавиатуру
        buttons = [
            [InlineKeyboardButton("❌ Ошибка загрузки моделей", callback_data="select_ai_provider")],
            [InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")]
        ]
        return InlineKeyboardMarkup(buttons)

def top5_model_info_keyboard(model_id: str, model_name: str) -> InlineKeyboardMarkup:
    """Создать клавиатуру с информацией о выбранной топ-5 модели"""
    buttons = [
        [InlineKeyboardButton("✅ Выбрать эту модель", callback_data=f"confirm_top5_model:{model_id}")],
        [InlineKeyboardButton("🔙 Назад к топ-5", callback_data="top5_models_selection")],
        [InlineKeyboardButton("📋 Все модели OpenRouter", callback_data="openrouter_model_selection")],
        [InlineKeyboardButton("🔙 Назад к провайдерам", callback_data="select_ai_provider")]
    ]
    return InlineKeyboardMarkup(buttons)

def ollama_model_selection_keyboard(available_models: List[str], current_model: str = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора модели Ollama"""
    buttons = []
    
    for model_name in available_models:
        # Определяем префикс в зависимости от текущего выбора
        if model_name == current_model:
            prefix = "✅ "
        else:
            prefix = "⚪ "
        
        # Ограничиваем длину названия модели для кнопки
        display_name = model_name
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        
        buttons.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"select_ollama_model:{model_name}"
        )])
    
    # Добавляем кнопку "Назад"
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")])
    
    return InlineKeyboardMarkup(buttons)

# Новые упрощенные клавиатуры для улучшения UX

def quick_actions_keyboard(selected_chat_id: str = None):
    """Меню быстрых действий"""
    keyboard = []
    
    if selected_chat_id:
        # Если чат выбран - показываем действия для него
        keyboard.extend([
            [InlineKeyboardButton("📝 Создать суммаризацию", callback_data=f"quick_create_{selected_chat_id}")],
            [InlineKeyboardButton("📋 Посмотреть суммаризации", callback_data=f"check_summary_{selected_chat_id}")],
            [InlineKeyboardButton("🔄 Загрузить сообщения", callback_data=f"load_messages_{selected_chat_id}")]
        ])
    else:
        # Предлагаем выбрать чат
        keyboard.append([InlineKeyboardButton("📊 Выбрать чат", callback_data="select_chat_for_action")])
    
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def chat_quick_menu_keyboard(vk_chat_id: str, group_id: int = None):
    """Упрощенное меню чата"""
    keyboard = [
        # Основные действия в одну строку
        [
            InlineKeyboardButton("📝 Создать", callback_data=f"quick_create_{vk_chat_id}"),
            InlineKeyboardButton("📋 Смотреть", callback_data=f"check_summary_{vk_chat_id}")
        ],
        [
            InlineKeyboardButton("🔄 Загрузить", callback_data=f"load_messages_{vk_chat_id}"),
            InlineKeyboardButton("📊 Статистика", callback_data=f"chat_stats_{vk_chat_id}")
        ],
        # Дополнительно
        [InlineKeyboardButton("🖼️ Анализ изображений", callback_data=f"image_analysis_menu_{vk_chat_id}")],
        [InlineKeyboardButton("📤 Опубликовать", callback_data=f"publish_menu_{vk_chat_id}")],
    ]
    
    # Определяем куда ведет кнопка "Назад" в зависимости от контекста
    if group_id:
        # Если мы в контексте конкретной группы, возвращаемся к главному меню группы
        keyboard.append([InlineKeyboardButton("🔙 К группе", callback_data=f"back_to_group_{group_id}")])
    else:
        # Если это общее меню, возвращаемся к выбору чатов
        keyboard.append([InlineKeyboardButton("🔙 Мои чаты", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def image_analysis_menu_keyboard(vk_chat_id: str, has_schedule: bool = False):
    """Меню анализа изображений"""
    keyboard = [
        [InlineKeyboardButton("▶️ Начать анализ", callback_data=f"start_image_analysis_{vk_chat_id}")],
        [InlineKeyboardButton("⚙️ Настройки анализа", callback_data=f"image_analysis_settings_{vk_chat_id}")],
    ]
    
    if has_schedule:
        keyboard.insert(1, [InlineKeyboardButton("📅 Показать анализ расписания", callback_data=f"show_schedule_analysis_{vk_chat_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад к чату", callback_data=f"quick_chat_{vk_chat_id}")])
    return InlineKeyboardMarkup(keyboard)

def image_analysis_settings_keyboard(vk_chat_id: str):
    """Клавиатура настроек анализа изображений"""
    keyboard = [
        [InlineKeyboardButton("🤖 Выбрать модель", callback_data=f"select_analysis_model_{vk_chat_id}")],
        [InlineKeyboardButton("📝 Изменить промпт", callback_data=f"change_analysis_prompt_{vk_chat_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"image_analysis_menu_{vk_chat_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_summary_keyboard(vk_chat_id: str, available_dates: list, show_all: bool = False):
    """Меню создания суммаризации"""
    keyboard = []
    
    # Показываем последние 3 даты или все
    dates_to_show = available_dates if show_all else available_dates[:3]
    
    for date in dates_to_show:
        date_str = date.date if hasattr(date, 'date') else date['date']
        count = date.count if hasattr(date, 'count') else date['count']
        keyboard.append([InlineKeyboardButton(
            f"📅 {date_str} ({count} сообщений)", 
            callback_data=f"create_for_date_{vk_chat_id}_{date_str}"
        )])
    
    # Больше дат (только если не показываем все)
    if not show_all and len(available_dates) > 3:
        keyboard.append([InlineKeyboardButton("📅 Все даты...", callback_data=f"all_dates_{vk_chat_id}")])
    
    # Выбор модели внизу
    keyboard.append([InlineKeyboardButton("🤖 Сменить модель", callback_data="select_model_for_analysis")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"quick_chat_{vk_chat_id}")])
    
    return InlineKeyboardMarkup(keyboard)


def settings_menu_keyboard():
    """Новое меню для настроек"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("❌ Удалить чат", callback_data="remove_chat")],
        [InlineKeyboardButton("🤖 AI провайдеры (детально)", callback_data="ai_provider_settings")],
        [InlineKeyboardButton("📅 Управление расписанием", callback_data="schedule_management")],
        [InlineKeyboardButton("🔄 Сменить группу", callback_data="change_group")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def schedule_management_keyboard(has_schedule: bool = False, has_analysis: bool = False):
    """Клавиатура управления расписанием группы"""
    keyboard = []
    
    if has_schedule:
        keyboard.append([InlineKeyboardButton("📅 Показать расписание", callback_data="show_schedule")])
        
        if has_analysis:
            keyboard.append([InlineKeyboardButton("📝 Показать полный текст", callback_data="show_full_schedule_text")])
        
        keyboard.append([InlineKeyboardButton("📤 Обновить расписание", callback_data="set_schedule")])
        keyboard.append([InlineKeyboardButton("🗑️ Удалить расписание", callback_data="delete_schedule")])
    else:
        keyboard.append([InlineKeyboardButton("📤 Установить расписание", callback_data="set_schedule")])
    
    keyboard.append([InlineKeyboardButton("🔙 К группе", callback_data="back_to_group_menu")])
    return InlineKeyboardMarkup(keyboard)

def publish_format_keyboard(vk_chat_id: str, date: str):
    """Клавиатура выбора формата публикации"""
    keyboard = [
        [InlineKeyboardButton("📝 Markdown формат", callback_data=f"publish_md_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🌐 HTML формат", callback_data=f"publish_html_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"publish_menu_{vk_chat_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def scenario_selection_keyboard(vk_chat_id: str, date: str):
    """Клавиатура выбора сценария суммаризации с новыми пресетами"""
    keyboard = [
        # Готовые пресеты
        [InlineKeyboardButton("⚡ Быстрая суммаризация", 
            callback_data=f"preset_fast_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🔄 С рефлексией", 
            callback_data=f"preset_reflection_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🧹 С очисткой данных", 
            callback_data=f"preset_cleaning_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🔍 Структурированный анализ", 
            callback_data=f"preset_structured_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("📅 С анализом расписания", 
            callback_data=f"preset_with_schedule_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🎯 Полный анализ", 
            callback_data=f"preset_full_{vk_chat_id}_{date}")],
        
        # Разделитель
        [InlineKeyboardButton("🎨 Конструктор (продвинутый)", 
            callback_data=f"custom_pipeline_{vk_chat_id}_{date}")],
        
        # Назад
        [InlineKeyboardButton("🔙 Назад", callback_data=f"quick_create_{vk_chat_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def custom_pipeline_keyboard(vk_chat_id: str, date: str, selected_steps: list):
    """Клавиатура конструктора пользовательского pipeline"""
    from domains.ai.models import StepType
    
    keyboard = []
    
    # Шаг 1: Очистка (опциональный)
    is_cleaning = StepType.CLEANING in selected_steps
    keyboard.append([InlineKeyboardButton(
        f"{'✅' if is_cleaning else '⬜'} 1. Очистка данных",
        callback_data=f"toggle_step_cleaning_{vk_chat_id}_{date}"
    )])
    
    # Шаг 2: Суммаризация (обязательный, всегда включен)
    keyboard.append([InlineKeyboardButton(
        "✅ 2. Суммаризация (обязательный)",
        callback_data="noop"  # Не кликабельно
    )])
    
    # Шаг 3: Рефлексия (опциональный)
    is_reflection = StepType.REFLECTION in selected_steps
    keyboard.append([InlineKeyboardButton(
        f"{'✅' if is_reflection else '⬜'} 3. Рефлексия",
        callback_data=f"toggle_step_reflection_{vk_chat_id}_{date}"
    )])
    
    # Шаг 4: Улучшение (зависит от рефлексии)
    is_improvement = StepType.IMPROVEMENT in selected_steps
    can_improve = is_reflection
    keyboard.append([InlineKeyboardButton(
        f"{'✅' if is_improvement else '⬜'} 4. Улучшение {'(требует рефлексию)' if not can_improve else ''}",
        callback_data=f"toggle_step_improvement_{vk_chat_id}_{date}" if can_improve else "noop"
    )])
    
    # Шаг 5: Анализ расписания (НОВОЕ)
    is_schedule = StepType.SCHEDULE_ANALYSIS in selected_steps
    keyboard.append([InlineKeyboardButton(
        f"{'✅' if is_schedule else '⬜'} 5. Анализ расписания",
        callback_data=f"toggle_step_schedule_analysis_{vk_chat_id}_{date}"
    )])
    
    # Шаг 6: Структурный анализ (опциональный)
    is_structured = StepType.CLASSIFICATION in selected_steps
    keyboard.append([InlineKeyboardButton(
        f"{'✅' if is_structured else '⬜'} 6. Структурный анализ",
        callback_data=f"toggle_step_structured_{vk_chat_id}_{date}"
    )])
    
    # Оценка времени
    estimated_time = len(selected_steps) * 30  # секунд на шаг
    keyboard.append([InlineKeyboardButton(
        f"📊 Предпросмотр: {len(selected_steps)} шагов, ~{estimated_time}с",
        callback_data="noop"
    )])
    
    # Действия
    keyboard.extend([
        [InlineKeyboardButton("💾 Сохранить как пресет", callback_data=f"save_custom_preset_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🚀 Запустить анализ", callback_data=f"run_custom_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"select_scenario_{vk_chat_id}_{date}")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def model_selection_for_summary_keyboard(vk_chat_id: str, date: str, scenario: str):
    """Клавиатура выбора модели с возможностью быстрого запуска"""
    keyboard = [
        [InlineKeyboardButton("✅ Запустить с текущей моделью", 
            callback_data=f"run_summary_{vk_chat_id}_{date}_{scenario}")],
        [InlineKeyboardButton("🤖 Изменить модель", 
            callback_data=f"change_model_for_summary_{vk_chat_id}_{date}_{scenario}")],
        [InlineKeyboardButton("🔙 Назад к выбору сценария", 
            callback_data=f"create_for_date_{vk_chat_id}_{date}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def summary_result_keyboard(vk_chat_id: str, date: str):
    """Клавиатура для результата суммаризации"""
    keyboard = [
        [InlineKeyboardButton("📤 Опубликовать (Markdown)", callback_data=f"publish_md_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("📤 Опубликовать (HTML)", callback_data=f"publish_html_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("🔙 К чату", callback_data=f"select_chat_{vk_chat_id}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def summary_view_keyboard(vk_chat_id: str, date: str, show_recreate: bool = True):
    """
    Клавиатура для просмотра существующей суммаризации
    
    Args:
        vk_chat_id: ID чата VK MAX
        date: Дата суммаризации (YYYY-MM-DD)
        show_recreate: Показывать ли кнопку пересоздания
    
    Returns:
        InlineKeyboardMarkup с кнопками действий
    """
    keyboard = [
        [InlineKeyboardButton("📤 Опубликовать (Markdown)", callback_data=f"publish_md_{vk_chat_id}_{date}")],
        [InlineKeyboardButton("📤 Опубликовать (HTML)", callback_data=f"publish_html_{vk_chat_id}_{date}")],
    ]
    
    if show_recreate:
        keyboard.append([InlineKeyboardButton("🔄 Пересоздать суммаризацию", callback_data=f"recreate_summary_{vk_chat_id}_{date}")])
    
    keyboard.extend([
        [InlineKeyboardButton("🔙 К списку дат", callback_data=f"check_summary_{vk_chat_id}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="back_to_main")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def admin_settings_keyboard():
    """Клавиатура настроек администратора"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📝 Логирование", callback_data="toggle_logging")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
