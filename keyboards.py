"""
Клавиатуры для Telegram бота
"""
import json
import os
from typing import List, Dict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from utils import shorten_callback_data

def main_menu_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("📊 Управление чатами", callback_data="manage_chats")],
        [InlineKeyboardButton("📈 Статистика", callback_data="statistics")],
        [InlineKeyboardButton("🤖 AI Модели", callback_data="select_ai_provider")],
        [InlineKeyboardButton("🔧 Настройки", callback_data="settings")],
        [InlineKeyboardButton("🔄 Сменить группу", callback_data="change_group")]
    ]
    return InlineKeyboardMarkup(keyboard)

def group_selection_keyboard(groups: list):
    """Клавиатура выбора группы"""
    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(
            f"📱 {group['group_name']}", 
            callback_data=f"select_group_{group['group_id']}"
        )])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)

def chat_management_keyboard():
    """Клавиатура управления чатами"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")],
        [InlineKeyboardButton("❌ Удалить чат", callback_data="remove_chat")],
        [InlineKeyboardButton("📋 Список чатов", callback_data="list_chats")],
        [InlineKeyboardButton("⚙️ Настройки чата", callback_data="chat_settings")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def chat_list_keyboard(chats: list):
    """Клавиатура списка чатов"""
    keyboard = []
    for chat in chats:
        keyboard.append([InlineKeyboardButton(
            f"💬 {chat['chat_name']}", 
            callback_data=f"select_chat_{chat['chat_id']}"
        )])
    
    # Добавляем кнопку добавления чата
    keyboard.append([InlineKeyboardButton("➕ Добавить чат", callback_data="add_chat")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_manage_chats")])
    return InlineKeyboardMarkup(keyboard)

def chat_settings_keyboard(vk_chat_id: str):
    """Клавиатура настроек чата"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data=f"chat_stats_{vk_chat_id}")],
        [InlineKeyboardButton("🔄 Загрузить сообщения", callback_data=f"load_messages_{vk_chat_id}")],
        [InlineKeyboardButton("📋 Проверить суммаризацию", callback_data=f"check_summary_{vk_chat_id}")],
        [InlineKeyboardButton("📤 Вывести в группу", callback_data=f"publish_summary_{vk_chat_id}")],
        [InlineKeyboardButton("📤 Вывести в группу (HTML)", callback_data=f"publish_summary_html_{vk_chat_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_manage_chats")]
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

def date_selection_keyboard(dates: list):
    """Клавиатура выбора даты"""
    keyboard = []
    for date in dates:
        keyboard.append([InlineKeyboardButton(
            f"📅 {date['date']} ({date['count']} сообщений)", 
            callback_data=f"select_date_{date['date']}"
        )])
    keyboard.append([InlineKeyboardButton("🤖 Выбрать модель для анализа", callback_data="select_model_for_analysis")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_settings")])
    return InlineKeyboardMarkup(keyboard)

def available_chats_keyboard(chats: list, page: int = 0, per_page: int = 10):
    """Клавиатура выбора доступных чатов VK MAX"""
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
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"select_available_chat_{chat['id']}"
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
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_manage_chats")])
    
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
        'gemini': '💎 Gemini'
    }
    
    # Создаем словарь статусов провайдеров
    provider_status = {}
    if provider_info:
        for info in provider_info:
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
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_management")])
    return InlineKeyboardMarkup(buttons)

def ai_provider_settings_keyboard(user_preferences: Dict = None) -> InlineKeyboardMarkup:
    """Создать клавиатуру для настроек AI провайдера"""
    buttons = [
        [InlineKeyboardButton("🎯 Выбрать модель", callback_data="select_ai_provider")],
        [InlineKeyboardButton("⚙️ Настройки по умолчанию", callback_data="ai_provider_defaults")],
        [InlineKeyboardButton("📊 Статус провайдеров", callback_data="ai_provider_status")],
        [InlineKeyboardButton("🔍 Проверить доступность", callback_data="check_providers_availability")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

def ai_provider_defaults_keyboard(current_default: str = 'gigachat') -> InlineKeyboardMarkup:
    """Создать клавиатуру для выбора провайдера по умолчанию"""
    buttons = []
    
    provider_display_names = {
        'gigachat': '🤖 GigaChat',
        'chatgpt': '🧠 ChatGPT', 
        'openrouter': '🔗 OpenRouter',
        'gemini': '💎 Gemini'
    }
    
    for provider, display_name in provider_display_names.items():
        prefix = "✅ " if provider == current_default else "⚪ "
        buttons.append([InlineKeyboardButton(
            f"{prefix}{display_name}",
            callback_data=f"set_default_provider:{provider}"
        )])
    
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")])
    return InlineKeyboardMarkup(buttons)

def confirm_ai_provider_change_keyboard(provider_name: str) -> InlineKeyboardMarkup:
    """Создать клавиатуру подтверждения смены провайдера"""
    provider_display_names = {
        'gigachat': 'GigaChat',
        'chatgpt': 'ChatGPT',
        'openrouter': 'OpenRouter', 
        'gemini': 'Gemini'
    }
    
    display_name = provider_display_names.get(provider_name, provider_name.title())
    
    buttons = [
        [InlineKeyboardButton(f"✅ Да, использовать {display_name}", callback_data=f"confirm_provider:{provider_name}")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_provider_change")],
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
