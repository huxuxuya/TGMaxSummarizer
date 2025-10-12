"""
Вспомогательные функции для Telegram бота
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re

logger = logging.getLogger(__name__)

def format_message_for_telegram(text: str, max_length: int = 4096) -> List[str]:
    """Разбить длинное сообщение на части для Telegram"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    # Разбиваем по абзацам
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
                # Абзац слишком длинный, разбиваем по предложениям
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
                            # Предложение слишком длинное, обрезаем
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

def escape_markdown_v2(text: str) -> str:
    """Экранировать символы для MarkdownV2 в Telegram"""
    import re
    
    # Символы, которые нужно экранировать для MarkdownV2, исключая те, что используются для форматирования
    escape_chars = r'[]()~`>#+-=|{}.!'
    
    # Используем регулярное выражение для экранирования, но исключаем экранирование точек в обычном тексте
    escaped_text = re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
    
    # Специальная обработка для точек только в начале строк, если они выглядят как часть нумерованного списка
    lines = escaped_text.split('\n')
    for i, line in enumerate(lines):
        if line.strip() and re.match(r'^\s*\d+\.', line):
            lines[i] = re.sub(r'(\d+)\.', r'\1\\.', line, 1)
    return '\n'.join(lines)

def format_summary_for_telegram(summary: str, date: str = None, chat_name: str = None) -> List[str]:
    """Форматировать суммаризацию для отправки в Telegram с MarkdownV2 разметкой"""
    # Сначала форматируем суммаризацию для MarkdownV2
    formatted_summary = format_summary_markdown_v2(summary)
    
    # Добавляем заголовок с датой, днем недели и названием чата
    if date:
        from datetime import datetime
        try:
            # Парсим дату
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            # Получаем день недели на русском
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            weekday = weekdays[date_obj.weekday()]
            # Форматируем дату для отображения
            formatted_date = date_obj.strftime('%d.%m.%Y')
            
            # Формируем компактный заголовок
            if chat_name:
                header = f"📱 *{chat_name}* • {formatted_date}, {weekday}\n\n"
            else:
                header = f"📋 *Информация от {formatted_date}, {weekday}*\n\n"
        except:
            if chat_name:
                header = f"📱 *{chat_name}* • {date}\n\n"
            else:
                header = f"📋 *Информация от {date}*\n\n"
    else:
        if chat_name:
            header = f"📱 *{chat_name}*\n\n"
        else:
            header = "📋 *Информация для ознакомления*\n\n"
    
    # Комбинируем заголовок и текст без дополнительного экранирования
    final_text = header + formatted_summary
    
    # Разбиваем на части
    parts = format_message_for_telegram(final_text)
    
    return parts

def format_summary_markdown_v2(summary: str) -> str:
    """Форматировать суммаризацию для MarkdownV2 в Telegram"""
    lines = summary.split('\n')
    formatted_lines = []
    
    for line in lines:
        original_line = line
        line_stripped = line.strip()
        
        # Обрабатываем заголовки секций - конвертируем в жирный текст для MarkdownV2
        if line_stripped.startswith('## 🚨 ТРЕБУЕТ ДЕЙСТВИЙ:'):
            formatted_lines.append('*🚨 ТРЕБУЕТ ДЕЙСТВИЙ:*')
        elif line_stripped.startswith('## 📋 НОВЫЕ ПРАВИЛА:'):
            formatted_lines.append('*📋 НОВЫЕ ПРАВИЛА:*')
        elif line_stripped.startswith('## 📅 МЕРОПРИЯТИЯ:'):
            formatted_lines.append('*📅 МЕРОПРИЯТИЯ:*')
        elif line_stripped.startswith('## ⚠️ ПРОБЛЕМЫ:'):
            formatted_lines.append('*⚠️ ПРОБЛЕМЫ:*')
        # Обрабатываем другие заголовки ## - конвертируем в жирный текст
        elif line_stripped.startswith('## '):
            header_text = line_stripped[3:].strip()  # Убираем ##
            formatted_lines.append(f'*{header_text}*')
        # Обрабатываем элементы списка с сохранением отступов
        elif line_stripped.startswith('- '):
            # Подсчитываем количество пробелов в начале строки для отступа
            indent_count = len(line) - len(line.lstrip())
            indent_spaces = ' ' * indent_count
            
            item_text = line_stripped[2:].strip()
            if item_text:
                # Конвертируем **жирный** в *жирный* для MarkdownV2
                item_text = item_text.replace('**', '*')
                # Сохраняем отступ и добавляем маркер списка
                formatted_lines.append(f"{indent_spaces}• {item_text}")
        # Обрабатываем пустые строки
        elif not line_stripped:
            formatted_lines.append('')
        # Обычный текст - конвертируем ** в * для MarkdownV2, сохраняя отступы
        else:
            if original_line:
                # Конвертируем **жирный** в *жирный* для MarkdownV2
                converted_line = original_line.replace('**', '*')
                formatted_lines.append(converted_line)
    
    return '\n'.join(formatted_lines)

def validate_chat_id(chat_id: str) -> bool:
    """Проверить валидность ID чата"""
    try:
        # ID чата должен быть числом
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
    
    # Сокращаем длинные сообщения об ошибках
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
    """
    Сокращает callback_data до максимальной длины, сохраняя важную информацию
    
    Args:
        callback_data: Исходный callback_data
        max_length: Максимальная длина (по умолчанию 60, оставляем запас от лимита 64)
    
    Returns:
        Сокращенный callback_data
    """
    if len(callback_data) <= max_length:
        return callback_data
    
    # Если это callback с model_id, попробуем сократить model_id
    if ':' in callback_data:
        prefix, model_id = callback_data.split(':', 1)
        
        # Вычисляем максимальную длину для model_id
        max_model_id_length = max_length - len(prefix) - 1  # -1 для ':'
        
        if len(model_id) > max_model_id_length:
            # Сокращаем model_id, оставляя начало и конец
            if max_model_id_length < 10:
                # Если очень мало места, берем только начало
                shortened_model_id = model_id[:max_model_id_length]
            else:
                # Берем начало и конец
                start_length = max_model_id_length // 2
                end_length = max_model_id_length - start_length - 3  # -3 для '...'
                shortened_model_id = model_id[:start_length] + '...' + model_id[-end_length:]
            
            return f"{prefix}:{shortened_model_id}"
    
    # Если не удалось сократить по-умному, просто обрезаем
    return callback_data[:max_length]

def format_summary_for_telegram_html(summary: str, date: str = None, chat_name: str = None) -> List[str]:
    """Форматировать суммаризацию для отправки в Telegram с HTML разметкой и collapsed block quotation"""
    from telegram_formatter import TelegramFormatter
    
    # Сначала форматируем суммаризацию для HTML
    formatted_summary = format_summary_html(summary)
    
    # Добавляем заголовок с датой, днем недели и названием чата
    if date:
        from datetime import datetime
        try:
            # Парсим дату
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            # Получаем день недели на русском
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            weekday = weekdays[date_obj.weekday()]
            # Форматируем дату для отображения
            formatted_date = date_obj.strftime('%d.%m.%Y')
            
            # Формируем компактный заголовок с HTML разметкой
            if chat_name:
                escaped_chat_name = TelegramFormatter.escape_html(chat_name)
                escaped_date = TelegramFormatter.escape_html(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html(weekday)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}, {escaped_weekday}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html(weekday)
                header = f"📋 <b>Информация от {escaped_date}, {escaped_weekday}</b>\n\n"
        except:
            if chat_name:
                escaped_chat_name = TelegramFormatter.escape_html(chat_name)
                escaped_date = TelegramFormatter.escape_html(date)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html(date)
                header = f"📋 <b>Информация от {escaped_date}</b>\n\n"
    else:
        if chat_name:
            escaped_chat_name = TelegramFormatter.escape_html(chat_name)
            header = f"📱 <b>{escaped_chat_name}</b>\n\n"
        else:
            header = "📋 <b>Информация для ознакомления</b>\n\n"
    
    # Создаем collapsed block quotation для суммаризации
    collapsed_summary = f'<blockquote expandable>\n{formatted_summary}\n</blockquote>'
    
    # Комбинируем заголовок и collapsed суммаризацию
    final_text = header + collapsed_summary
    
    # Разбиваем на части
    parts = format_message_for_telegram(final_text)
    
    return parts

def format_summary_html(summary: str) -> str:
    """Форматировать суммаризацию для HTML в Telegram"""
    from telegram_formatter import TelegramFormatter
    
    lines = summary.split('\n')
    formatted_lines = []
    
    for line in lines:
        original_line = line
        line_stripped = line.strip()
        
        # Обрабатываем заголовки секций - конвертируем в жирный текст для HTML
        if line_stripped.startswith('## 🚨 ТРЕБУЕТ ДЕЙСТВИЙ:'):
            formatted_lines.append('<b>🚨 ТРЕБУЕТ ДЕЙСТВИЙ:</b>')
        elif line_stripped.startswith('## 📋 НОВЫЕ ПРАВИЛА:'):
            formatted_lines.append('<b>📋 НОВЫЕ ПРАВИЛА:</b>')
        elif line_stripped.startswith('## 📅 МЕРОПРИЯТИЯ:'):
            formatted_lines.append('<b>📅 МЕРОПРИЯТИЯ:</b>')
        elif line_stripped.startswith('## ⚠️ ПРОБЛЕМЫ:'):
            formatted_lines.append('<b>⚠️ ПРОБЛЕМЫ:</b>')
        # Обрабатываем другие заголовки ## - конвертируем в жирный текст
        elif line_stripped.startswith('## '):
            header_text = line_stripped[3:].strip()  # Убираем ##
            escaped_header = TelegramFormatter.escape_html(header_text)
            formatted_lines.append(f'<b>{escaped_header}</b>')
        # Обрабатываем элементы списка с сохранением отступов
        elif line_stripped.startswith('- '):
            # Подсчитываем количество пробелов в начале строки для отступа
            indent_count = len(line) - len(line.lstrip())
            indent_spaces = ' ' * indent_count
            
            item_text = line_stripped[2:].strip()
            if item_text:
                # Конвертируем **жирный** в <b>жирный</b> для HTML
                # Используем более надежный способ замены
                import re
                item_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', item_text)
                # Экранируем HTML символы
                escaped_item = TelegramFormatter.escape_html(item_text)
                # Восстанавливаем теги жирного текста после экранирования
                escaped_item = escaped_item.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                # Сохраняем отступ и добавляем маркер списка
                formatted_lines.append(f"{indent_spaces}• {escaped_item}")
        # Обрабатываем пустые строки
        elif not line_stripped:
            formatted_lines.append('')
        # Обычный текст - конвертируем ** в <b></b> для HTML, сохраняя отступы
        else:
            if original_line:
                # Конвертируем **жирный** в <b>жирный</b> для HTML
                # Используем более надежный способ замены
                import re
                converted_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', original_line)
                # Экранируем HTML символы
                escaped_line = TelegramFormatter.escape_html(converted_line)
                # Восстанавливаем теги жирного текста после экранирования
                escaped_line = escaped_line.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                formatted_lines.append(escaped_line)
    
    return '\n'.join(formatted_lines)

def format_summary_for_telegram_html_universal(summary: str, date: str = None, chat_name: str = None) -> List[str]:
    """Форматировать суммаризацию для отправки в Telegram с универсальным HTML преобразованием"""
    from telegram_formatter import TelegramFormatter
    
    # Используем универсальное преобразование Markdown в HTML
    formatted_summary = TelegramFormatter.markdown_to_html_universal(summary, telegram_safe=True)
    
    # Добавляем заголовок с датой, днем недели и названием чата
    if date:
        from datetime import datetime
        try:
            # Парсим дату
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            # Получаем день недели на русском
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            weekday = weekdays[date_obj.weekday()]
            # Форматируем дату для отображения
            formatted_date = date_obj.strftime('%d.%m.%Y')
            
            # Формируем компактный заголовок с HTML разметкой
            if chat_name:
                escaped_chat_name = TelegramFormatter.escape_html(chat_name)
                escaped_date = TelegramFormatter.escape_html(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html(weekday)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}, {escaped_weekday}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html(weekday)
                header = f"📋 <b>Информация от {escaped_date}, {escaped_weekday}</b>\n\n"
        except:
            if chat_name:
                escaped_chat_name = TelegramFormatter.escape_html(chat_name)
                escaped_date = TelegramFormatter.escape_html(date)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html(date)
                header = f"📋 <b>Информация от {escaped_date}</b>\n\n"
    else:
        if chat_name:
            escaped_chat_name = TelegramFormatter.escape_html(chat_name)
            header = f"📱 <b>{escaped_chat_name}</b>\n\n"
        else:
            header = "📋 <b>Информация для ознакомления</b>\n\n"
    
    # Создаем collapsed block quotation для суммаризации
    collapsed_summary = f'<blockquote expandable>\n{formatted_summary}\n</blockquote>'
    
    # Комбинируем заголовок и collapsed суммаризацию
    final_text = header + collapsed_summary
    
    # Разбиваем на части
    parts = format_message_for_telegram(final_text)
    
    return parts
