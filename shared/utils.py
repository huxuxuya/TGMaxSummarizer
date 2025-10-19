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


def format_chat_stats(stats) -> str:
    """Форматировать статистику чата для отображения"""
    text = f"📊 *Статистика* чата\n\n"
    text += f"• Всего сообщений: {stats.total_messages}\n"
    text += f"• Дней загружено: {stats.days_count}\n"
    text += f"• Изображений: {stats.total_images} (проанализировано: {stats.analyzed_images})\n"
    
    if stats.unanalyzed_images > 0:
        text += f"• ⚠️ Не проанализировано: {stats.unanalyzed_images} изображений\n"
    
    text += "\n"
    
    if stats.recent_days:
        text += "📅 *Последние дни:*\n"
        for day in stats.recent_days[:5]:
            date_display = format_date_for_display(day['date'])
            text += f"• {date_display} ({day['count']} сообщений)\n"
    
    if stats.recent_analysis_dates:
        text += "\n🖼️ *Последние анализы изображений:*\n"
        for day in stats.recent_analysis_dates[:5]:
            date_display = format_date_for_display(day['date'])
            text += f"• {date_display} ({day['count']} изображений)\n"
    
    return text


def format_error_message(error: Exception) -> str:
    """Форматировать сообщение об ошибке для Telegram с экранированием Markdown"""
    from infrastructure.telegram.formatter import TelegramFormatter
    
    error_msg = str(error)
    
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."
    
    # Экранируем специальные символы Markdown
    error_msg = TelegramFormatter.escape_markdown_v1(error_msg)
    
    return f"❌ Ошибка: {error_msg}"

def format_success_message(message: str) -> str:
    """Форматировать сообщение об успехе"""
    return f"✅ {message}"


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
    """
    Получить отображаемое имя отправителя с учетом специальных пользователей
    
    Args:
        sender_id: ID отправителя
        sender_name: Имя отправителя по умолчанию
        
    Returns:
        Отформатированное имя для отображения
    """
    from core.app_context import get_app_context
    ctx = get_app_context()
    SPECIAL_USERS = ctx.config['bot'].special_users
    
    # Проверяем, является ли пользователь специальным
    if sender_id in SPECIAL_USERS:
        return SPECIAL_USERS[sender_id]
    
    # Иначе возвращаем имя по умолчанию
    if sender_name:
        return sender_name
    
    return f"User {sender_id}" if sender_id else "Unknown"

def get_sender_display_name_with_id(sender_id: int, sender_name: str = None, time_str: str = None) -> str:
    """
    Получить отображаемое имя отправителя с ID и временем, 
    но для Виктории Романовны оставить как есть
    
    Args:
        sender_id: ID отправителя
        sender_name: Имя отправителя по умолчанию
        time_str: Время сообщения
        
    Returns:
        Отформатированное имя для отображения с ID и временем
    """
    from core.app_context import get_app_context
    ctx = get_app_context()
    SPECIAL_USERS = ctx.config['bot'].special_users
    
    # Для Виктории Романовны оставляем как есть (без ID и времени)
    if sender_id in SPECIAL_USERS:
        return SPECIAL_USERS[sender_id]
    
    # Для остальных пользователей добавляем ID и время
    # Если sender_name это 'Неизвестно' или None, используем User + ID
    if sender_name and sender_name != 'Неизвестно':
        display_name = f"{sender_name} (ID:{sender_id})"
    else:
        display_name = f"User {sender_id}"
    
    # Добавляем время если оно есть и не равно '??:??'
    if time_str and time_str != '??:??':
        return f"[{time_str}] {display_name}"
    else:
        return display_name

def format_summary_for_telegram(summary: str, date: str = None, chat_name: str = None) -> List[str]:
    """Форматировать суммаризацию для отправки в Telegram используя telegramify-markdown"""
    from infrastructure.telegram.sender import TelegramMessageSender
    from infrastructure.telegram.formatter import TelegramFormatter
    
    # Добавляем заголовок с датой, днем недели и названием чата в стандартном Markdown
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
            
            # Формируем компактный заголовок в стандартном Markdown
            if chat_name:
                header = f"📱 **{chat_name}** • {formatted_date}, {weekday}\n\n"
            else:
                header = f"📋 **Информация от {formatted_date}, {weekday}**\n\n"
        except:
            if chat_name:
                header = f"📱 **{chat_name}** • {date}\n\n"
            else:
                header = f"📋 **Информация от {date}**\n\n"
    else:
        if chat_name:
            header = f"📱 **{chat_name}**\n\n"
        else:
            header = "📋 **Информация для ознакомления**\n\n"
    
    # Комбинируем заголовок и текст в стандартном Markdown
    final_text = header + summary
    
    # Конвертируем в Telegram MarkdownV2 через telegramify-markdown
    telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(final_text)
    
    # Разбиваем на части
    parts = TelegramFormatter.split_message(telegram_text)
    
    return parts

def format_summary_html(summary: str) -> str:
    """Форматировать суммаризацию для HTML в Telegram"""
    from infrastructure.telegram.formatter import TelegramFormatter
    
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
    from infrastructure.telegram.formatter import TelegramFormatter
    
    
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
                escaped_chat_name = TelegramFormatter.escape_html_content(chat_name)
                escaped_date = TelegramFormatter.escape_html_content(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html_content(weekday)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}, {escaped_weekday}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html_content(formatted_date)
                escaped_weekday = TelegramFormatter.escape_html_content(weekday)
                header = f"📋 <b>Информация от {escaped_date}, {escaped_weekday}</b>\n\n"
        except:
            if chat_name:
                escaped_chat_name = TelegramFormatter.escape_html_content(chat_name)
                escaped_date = TelegramFormatter.escape_html_content(date)
                header = f"📱 <b>{escaped_chat_name}</b> • {escaped_date}\n\n"
            else:
                escaped_date = TelegramFormatter.escape_html_content(date)
                header = f"📋 <b>Информация от {escaped_date}</b>\n\n"
    else:
        if chat_name:
            escaped_chat_name = TelegramFormatter.escape_html_content(chat_name)
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
