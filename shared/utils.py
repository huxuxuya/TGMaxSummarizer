import re
from typing import List, Dict, Any
from datetime import datetime, timedelta

def format_message_for_telegram(text: str, max_length: int = 4096) -> List[str]:
    """Разбить длинное сообщение на части для Telegram"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_part) + len(paragraph) + 2 <= max_length:
            if current_part:
                current_part += '\n\n' + paragraph
            else:
                current_part = paragraph
        else:
            if current_part:
                parts.append(current_part)
                current_part = paragraph
            else:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    if len(current_part) + len(sentence) + 1 <= max_length:
                        if current_part:
                            current_part += ' ' + sentence
                        else:
                            current_part = sentence
                    else:
                        if current_part:
                            parts.append(current_part)
                            current_part = sentence
                        else:
                            parts.append(sentence[:max_length-3] + "...")
    
    if current_part:
        parts.append(current_part)
    
    return parts

def format_date_for_display(date_str: str) -> str:
    """Форматировать дату для отображения"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_str

def format_time_for_display(timestamp: int) -> str:
    """Форматировать время для отображения"""
    try:
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%H:%M")
    except (ValueError, OSError):
        return "??:??"

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def format_chat_stats(stats: Dict) -> str:
    """Форматировать статистику чата для отображения"""
    text = f"📊 *Статистика* чата\n\n"
    text += f"• Всего сообщений: {stats.get('total_messages', 0)}\n"
    text += f"• Дней загружено: {stats.get('days_count', 0)}\n\n"
    
    if stats.get('recent_days'):
        text += "📅 *Последние дни:*\n"
        for day in stats['recent_days'][:5]:
            date_display = format_date_for_display(day['date'])
            text += f"• {date_display} ({day['count']} сообщений)\n"
    
    return text

def validate_chat_id(chat_id: str) -> bool:
    """Проверить валидность ID чата"""
    try:
        int(chat_id)
        return True
    except ValueError:
        return False

def get_date_range(days: int = 7) -> List[str]:
    """Получить список дат за последние дни"""
    dates = []
    today = datetime.now().date()
    
    for i in range(days):
        date = today - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    return dates

def format_error_message(error: Exception) -> str:
    """Форматировать сообщение об ошибке"""
    error_msg = str(error)
    
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."
    
    return f"❌ Ошибка: {error_msg}"

def format_success_message(message: str) -> str:
    """Форматировать сообщение об успехе"""
    return f"✅ {message}"

def format_info_message(message: str) -> str:
    """Форматировать информационное сообщение"""
    return f"ℹ️ {message}"

def format_warning_message(message: str) -> str:
    """Форматировать предупреждение"""
    return f"⚠️ {message}"

def shorten_callback_data(callback_data: str, max_length: int = 60) -> str:
    """Сокращает callback_data до максимальной длины"""
    if len(callback_data) <= max_length:
        return callback_data
    
    if ':' in callback_data:
        prefix, model_id = callback_data.split(':', 1)
        max_model_id_length = max_length - len(prefix) - 1
        
        if len(model_id) > max_model_id_length:
            if max_model_id_length < 10:
                shortened_model_id = model_id[:max_model_id_length]
            else:
                start_length = max_model_id_length // 2
                end_length = max_model_id_length - start_length - 3
                shortened_model_id = model_id[:start_length] + '...' + model_id[-end_length:]
            
            return f"{prefix}:{shortened_model_id}"
    
    return callback_data[:max_length]

def get_sender_display_name(sender_id: int, sender_name: str = None) -> str:
    """Получить отображаемое имя отправителя"""
    special_users = {
        44502596: "Виктория Романовна(учитель)"
    }
    
    if sender_id in special_users:
        return special_users[sender_id]
    
    if sender_name:
        return sender_name
    
    return f"User {sender_id}" if sender_id else "Unknown"
