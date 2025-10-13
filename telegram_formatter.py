"""
Модуль для безопасного форматирования текста для Telegram Bot API
Поддерживает MarkdownV2 и HTML режимы
"""
import re
import logging
from typing import Optional, List, Union
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

class TelegramFormatter:
    """Класс для безопасного форматирования текста для Telegram"""
    
    # Символы, которые нужно экранировать в MarkdownV2
    MARKDOWN_V2_ESCAPE_CHARS = [
        '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', 
        '+', '-', '=', '|', '{', '}', '.', '!'
    ]
    
    # Символы, которые нужно экранировать в обычном Markdown
    MARKDOWN_V1_ESCAPE_CHARS = ['_', '*', '`', '[']
    
    # Символы, которые нужно экранировать в HTML
    HTML_ESCAPE_CHARS = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """
        Экранирует специальные символы для MarkdownV2
        
        Args:
            text: Текст для экранирования
            
        Returns:
            Экранированный текст
        """
        if not text:
            return text
            
        escaped_text = text
        
        # Экранируем символы в правильном порядке (сначала обратные слеши)
        # чтобы избежать двойного экранирования
        if '\\' in escaped_text:
            escaped_text = escaped_text.replace('\\', '\\\\')
        
        # Затем экранируем остальные символы
        for char in TelegramFormatter.MARKDOWN_V2_ESCAPE_CHARS:
            if char != '\\':  # Уже обработали выше
                escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
    
    @staticmethod
    def escape_markdown_v1(text: str) -> str:
        """
        Экранирует специальные символы для обычного Markdown
        
        Args:
            text: Текст для экранирования
            
        Returns:
            Экранированный текст
        """
        if not text:
            return text
            
        escaped_text = text
        for char in TelegramFormatter.MARKDOWN_V1_ESCAPE_CHARS:
            escaped_text = escaped_text.replace(char, f'\\{char}')
        
        return escaped_text
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Экранирует специальные символы для HTML
        
        Args:
            text: Текст для экранирования
            
        Returns:
            Экранированный текст
        """
        if not text:
            return text
            
        escaped_text = text
        for char, replacement in TelegramFormatter.HTML_ESCAPE_CHARS.items():
            escaped_text = escaped_text.replace(char, replacement)
        
        return escaped_text
    
    @staticmethod
    def format_bold(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как жирный
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга (markdown_v2, markdown, html)
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode == "markdown_v2":
            escaped_text = TelegramFormatter.escape_markdown_v2(text)
            return f"*{escaped_text}*"
        elif parse_mode == "markdown":
            escaped_text = TelegramFormatter.escape_markdown_v1(text)
            return f"*{escaped_text}*"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<b>{escaped_text}</b>"
        else:
            return text
    
    @staticmethod
    def format_italic(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как курсив
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode == "markdown_v2":
            escaped_text = TelegramFormatter.escape_markdown_v2(text)
            return f"_{escaped_text}_"
        elif parse_mode == "markdown":
            escaped_text = TelegramFormatter.escape_markdown_v1(text)
            return f"_{escaped_text}_"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<i>{escaped_text}</i>"
        else:
            return text
    
    @staticmethod
    def format_underline(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как подчеркнутый
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode == "markdown_v2":
            escaped_text = TelegramFormatter.escape_markdown_v2(text)
            return f"__{escaped_text}__"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<u>{escaped_text}</u>"
        else:
            return text
    
    @staticmethod
    def format_strikethrough(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как зачеркнутый
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode == "markdown_v2":
            escaped_text = TelegramFormatter.escape_markdown_v2(text)
            return f"~{escaped_text}~"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<s>{escaped_text}</s>"
        else:
            return text
    
    @staticmethod
    def format_code(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как код
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode in ["markdown_v2", "markdown"]:
            escaped_text = TelegramFormatter.escape_markdown_v2(text) if parse_mode == "markdown_v2" else TelegramFormatter.escape_markdown_v1(text)
            return f"`{escaped_text}`"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<code>{escaped_text}</code>"
        else:
            return text
    
    @staticmethod
    def format_code_block(text: str, language: str = "", parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как блок кода
        
        Args:
            text: Текст для форматирования
            language: Язык программирования (опционально)
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if not text:
            return text
            
        if parse_mode in ["markdown_v2", "markdown"]:
            escaped_text = TelegramFormatter.escape_markdown_v2(text) if parse_mode == "markdown_v2" else TelegramFormatter.escape_markdown_v1(text)
            return f"```{language}\n{escaped_text}\n```"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<pre><code class='language-{language}'>{escaped_text}</code></pre>"
        else:
            return text
    
    @staticmethod
    def format_link(text: str, url: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует ссылку
        
        Args:
            text: Текст ссылки
            url: URL ссылки
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированная ссылка
        """
        if not text or not url:
            return text or url
            
        if parse_mode in ["markdown_v2", "markdown"]:
            escaped_text = TelegramFormatter.escape_markdown_v2(text) if parse_mode == "markdown_v2" else TelegramFormatter.escape_markdown_v1(text)
            escaped_url = TelegramFormatter.escape_markdown_v2(url) if parse_mode == "markdown_v2" else TelegramFormatter.escape_markdown_v1(url)
            return f"[{escaped_text}]({escaped_url})"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            escaped_url = TelegramFormatter.escape_html(url)
            return f"<a href='{escaped_url}'>{escaped_text}</a>"
        else:
            return text
    
    @staticmethod
    def format_heading(text: str, level: int = 1, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует заголовок
        
        Args:
            text: Текст заголовка
            level: Уровень заголовка (1-6)
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный заголовок
        """
        if not text:
            return text
            
        if parse_mode == "markdown_v2":
            escaped_text = TelegramFormatter.escape_markdown_v2(text)
            return f"{'#' * min(level, 6)} {escaped_text}"
        elif parse_mode == "html":
            escaped_text = TelegramFormatter.escape_html(text)
            return f"<h{min(level, 6)}>{escaped_text}</h{min(level, 6)}>"
        else:
            return text
    
    @staticmethod
    def format_list(items: List[str], ordered: bool = False, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует список
        
        Args:
            items: Список элементов
            ordered: Нумерованный ли список
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный список
        """
        if not items:
            return ""
            
        formatted_items = []
        for i, item in enumerate(items):
            if parse_mode in ["markdown_v2", "markdown"]:
                escaped_item = TelegramFormatter.escape_markdown_v2(item) if parse_mode == "markdown_v2" else TelegramFormatter.escape_markdown_v1(item)
                if ordered:
                    formatted_items.append(f"{i + 1}\\. {escaped_item}")
                else:
                    formatted_items.append(f"• {escaped_item}")
            elif parse_mode == "html":
                escaped_item = TelegramFormatter.escape_html(item)
                if ordered:
                    formatted_items.append(f"<li>{escaped_item}</li>")
                else:
                    formatted_items.append(f"<li>{escaped_item}</li>")
            else:
                formatted_items.append(item)
        
        if parse_mode == "html":
            tag = "ol" if ordered else "ul"
            return f"<{tag}>\n" + "\n".join(formatted_items) + f"\n</{tag}>"
        else:
            return "\n".join(formatted_items)
    
    @staticmethod
    def validate_markdown_v2(text: str) -> bool:
        """
        Проверяет валидность MarkdownV2 текста
        
        Args:
            text: Текст для проверки
            
        Returns:
            True если текст валиден, False иначе
        """
        try:
            # Простая проверка на парные символы
            pairs = [('*', '*'), ('_', '_'), ('__', '__'), ('~', '~'), ('`', '`')]
            
            for open_char, close_char in pairs:
                open_count = text.count(open_char)
                close_count = text.count(close_char)
                if open_count != close_count:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Ошибка валидации MarkdownV2: {e}")
            return False
    
    @staticmethod
    def safe_format(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Безопасно форматирует текст с обработкой ошибок
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Безопасно отформатированный текст
        """
        try:
            if parse_mode == "markdown_v2":
                if not TelegramFormatter.validate_markdown_v2(text):
                    logger.warning("MarkdownV2 текст не прошел валидацию, используем HTML")
                    return TelegramFormatter.escape_html(text)
                return text
            elif parse_mode == "html":
                return TelegramFormatter.escape_html(text)
            else:
                return text
        except Exception as e:
            logger.error(f"Ошибка форматирования текста: {e}")
            return text
    
    @staticmethod
    def split_long_message(text: str, max_length: int = 4096, parse_mode: str = "markdown_v2") -> List[str]:
        """
        Разбивает длинное сообщение на части
        
        Args:
            text: Текст для разбивки
            max_length: Максимальная длина части
            parse_mode: Режим парсинга
            
        Returns:
            Список частей сообщения
        """
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
                    # Если один абзац слишком длинный, разбиваем по предложениям
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        if len(current_part) + len(sentence) + 2 <= max_length:
                            if current_part:
                                current_part += '. ' + sentence
                            else:
                                current_part = sentence
                        else:
                            if current_part:
                                parts.append(current_part)
                                current_part = sentence
                            else:
                                # Если одно предложение слишком длинное, разбиваем принудительно
                                while len(sentence) > max_length:
                                    parts.append(sentence[:max_length])
                                    sentence = sentence[max_length:]
                                current_part = sentence
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    @staticmethod
    def format_analysis_result_with_reflection(analysis_result: dict, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует результат анализа с рефлексией в три раздела с цитатами
        
        Args:
            analysis_result: Словарь с результатами анализа
            parse_mode: Режим парсинга (markdown_v2, markdown, html)
            
        Returns:
            Отформатированный текст с тремя разделами
        """
        if not isinstance(analysis_result, dict):
            # Если это не словарь, возвращаем как есть
            return str(analysis_result)
        
        # Извлекаем компоненты
        original_summary = analysis_result.get('summary', '')
        reflection = analysis_result.get('reflection', '')
        improved_summary = analysis_result.get('improved', '')
        
        # Формируем заголовки
        if parse_mode == "markdown_v2":
            header1 = "*📝 Первый ответ модели:*"
            header2 = "*🤔 Результат рефлексии:*"
            header3 = "*✨ Финальная суммаризация:*"
            error_text = "*❌ Ошибка:*"
        elif parse_mode == "markdown":
            header1 = "*📝 Первый ответ модели:*"
            header2 = "*🤔 Результат рефлексии:*"
            header3 = "*✨ Финальная суммаризация:*"
            error_text = "*❌ Ошибка:*"
        elif parse_mode == "html":
            header1 = "<b>📝 Первый ответ модели:</b>"
            header2 = "<b>🤔 Результат рефлексии:</b>"
            header3 = "<b>✨ Финальная суммаризация:</b>"
            error_text = "<b>❌ Ошибка:</b>"
        else:
            header1 = "📝 Первый ответ модели:"
            header2 = "🤔 Результат рефлексии:"
            header3 = "✨ Финальная суммаризация:"
            error_text = "❌ Ошибка:"
        
        result_parts = []
        
        # Раздел 1: Первый ответ модели
        result_parts.append(header1)
        if original_summary:
            if parse_mode in ["markdown_v2", "markdown"]:
                # Используем блок цитаты
                quoted_text = TelegramFormatter._format_quote_block(original_summary, parse_mode)
            else:
                quoted_text = f"> {original_summary}"
            result_parts.append(quoted_text)
        else:
            result_parts.append(f"{error_text} Не удалось получить первый ответ модели")
        
        result_parts.append("")  # Пустая строка между разделами
        
        # Раздел 2: Результат рефлексии
        result_parts.append(header2)
        if reflection:
            if parse_mode in ["markdown_v2", "markdown"]:
                quoted_text = TelegramFormatter._format_quote_block(reflection, parse_mode)
            else:
                quoted_text = f"> {reflection}"
            result_parts.append(quoted_text)
        else:
            result_parts.append(f"{error_text} Рефлексия не была выполнена или завершилась с ошибкой")
        
        result_parts.append("")  # Пустая строка между разделами
        
        # Раздел 3: Финальная суммаризация
        result_parts.append(header3)
        if improved_summary:
            if parse_mode in ["markdown_v2", "markdown"]:
                quoted_text = TelegramFormatter._format_quote_block(improved_summary, parse_mode)
            else:
                quoted_text = f"> {improved_summary}"
            result_parts.append(quoted_text)
        else:
            result_parts.append(f"{error_text} Финальная суммаризация не была создана")
        
        return "\n".join(result_parts)
    
    @staticmethod
    def _format_quote_block(text: str, parse_mode: str = "markdown_v2") -> str:
        """
        Форматирует текст как блок цитаты
        
        Args:
            text: Текст для форматирования
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный блок цитаты
        """
        if not text:
            return ""
        
        if parse_mode == "markdown":
            # Для обычного Markdown используем символ цитаты без экранирования
            lines = text.split('\n')
            quoted_lines = []
            
            for line in lines:
                if line.strip():  # Если строка не пустая
                    quoted_lines.append(f"> {line}")
                else:  # Если строка пустая, оставляем как есть
                    quoted_lines.append("")
            
            return "\n".join(quoted_lines)
        else:
            # Для других режимов используем символ цитаты
            lines = text.split('\n')
            quoted_lines = []
            
            for line in lines:
                if parse_mode == "markdown_v2":
                    # НЕ экранируем здесь - это сделает safe_edit_message_text
                    # Просто добавляем символ цитаты (будет экранирован позже)
                    quoted_lines.append(f"> {line}")
                elif parse_mode == "html":
                    escaped_line = TelegramFormatter.escape_html(line)
                    quoted_lines.append(f"<blockquote>{escaped_line}</blockquote>")
                else:
                    quoted_lines.append(f"> {line}")
            
            return "\n".join(quoted_lines)
    
    @staticmethod
    def smart_escape_markdown_v2(text: str) -> str:
        """
        Умное экранирование для MarkdownV2 - сохраняет форматирование, но экранирует проблемные символы
        Обрабатывает блоки цитат (>) контекстно - не экранирует > в начале строки
        
        Args:
            text: Текст для экранирования
            
        Returns:
            Умно экранированный текст
        """
        if not text:
            return text
        
        # Улучшенная обработка форматирования
        import re
        
        # 1. Сначала конвертируем **text** (Markdown) в *text* (MarkdownV2) для жирного текста
        # Находим все пары **text** и заменяем на *text*
        bold_pattern = r'\*\*([^*\n]+)\*\*'
        text = re.sub(bold_pattern, r'*\1*', text)
        
        # 2. Обрабатываем курсивное форматирование _текст_
        # Находим все корректные пары _текст_ и временно заменяем их на плейсхолдеры
        placeholders = []
        # Более строгое регулярное выражение: _ должен быть окружен пробелами или знаками препинания
        italic_pattern = r'(?<![a-zA-Z0-9])_([^_\n]+)_(?![a-zA-Z0-9])'
        matches = list(re.finditer(italic_pattern, text))
        
        for i, match in enumerate(matches):
            inner_text = match.group(1).strip()
            if inner_text and len(inner_text) > 0:
                placeholder = f"__CURSIVE_{i}__"
                placeholders.append((placeholder, match.group(0)))
                text = text.replace(match.group(0), placeholder, 1)
        
        # 3. Восстанавливаем корректное курсивное форматирование ПЕРЕД экранированием
        for placeholder, original in placeholders:
            text = text.replace(placeholder, original)
        
        # 4. Теперь экранируем только проблемные _ (одиночные, которые могут вызвать ошибки парсинга)
        # НЕ экранируем _ внутри обычных слов (например, parse_mode, user_id)
        # Экранируем только одиночные _ или _ в начале/конце слов
        import re
        # Находим одиночные _ или _ в начале/конце слов, но не внутри слов
        text = re.sub(r'(?<![a-zA-Z0-9])_(?![a-zA-Z0-9])', r'\\_', text)
        
        # Символы, которые нужно экранировать для MarkdownV2
        # НЕ экранируем: *, ` (нужны для форматирования)
        # Экранируем: [, ], (, ), ~, ., !, -, +, =, |, {, }, # (могут вызвать проблемы)
        # > обрабатываем контекстно - не экранируем в начале строки (блоки цитат)
        # _ уже обработан выше
        # Добавляем длинный дефис – который может вызывать проблемы
        problematic_chars = ['[', ']', '(', ')', '~', '.', '!', '-', '+', '=', '|', '{', '}', '#', '–']
        
        # Обрабатываем построчно для сохранения блоков цитат
        lines = text.split('\n')
        escaped_lines = []
        
        for line in lines:
            # Проверяем, начинается ли строка с маркера блока цитаты
            if line.startswith('> '):
                # Это блок цитаты - НЕ экранируем ведущий >
                # Но экранируем содержимое строки
                quote_content = line[2:]  # Убираем префикс "> "
                escaped_content = TelegramFormatter._escape_text_content(quote_content, problematic_chars)
                escaped_lines.append(f"> {escaped_content}")
            else:
                # Обычная строка - экранируем все включая >
                escaped_line = TelegramFormatter._escape_text_content(line, problematic_chars + ['>'])
                escaped_lines.append(escaped_line)
        
        return '\n'.join(escaped_lines)
    
    @staticmethod
    def _escape_text_content(text: str, chars_to_escape: list) -> str:
        """
        Вспомогательная функция для экранирования текста
        
        Args:
            text: Текст для экранирования
            chars_to_escape: Список символов для экранирования
            
        Returns:
            Экранированный текст
        """
        if not text:
            return text
        
        result = text
        
        # Экранируем обратные слеши в первую очередь
        result = result.replace('\\', '\\\\')
        
        # Экранируем все символы из списка
        for char in chars_to_escape:
            result = result.replace(char, f'\\{char}')
        
        return result
    
    @staticmethod
    def markdown_to_html_universal(markdown_text: str, telegram_safe: bool = True) -> str:
        """
        Универсальное преобразование Markdown в HTML с использованием библиотеки markdown
        
        Args:
            markdown_text: Текст в формате Markdown
            telegram_safe: Если True, экранирует HTML символы для безопасного использования в Telegram
            
        Returns:
            HTML текст, готовый для использования в Telegram
        """
        try:
            import markdown
            
            # Создаем экземпляр markdown с настройками для Telegram
            md = markdown.Markdown(
                extensions=[
                    'markdown.extensions.extra',  # Включает таблицы, определения и другие расширения
                    'markdown.extensions.codehilite',  # Подсветка синтаксиса кода
                    'markdown.extensions.fenced_code',  # Fenced code blocks
                    'markdown.extensions.tables',  # Таблицы
                    'markdown.extensions.toc',  # Table of contents
                ],
                extension_configs={
                    'markdown.extensions.codehilite': {
                        'css_class': 'highlight'
                    }
                }
            )
            
            # Преобразуем Markdown в HTML
            html = md.convert(markdown_text)
            
            if telegram_safe:
                # Конвертируем стандартные HTML теги в теги, поддерживаемые Telegram
                # Telegram поддерживает: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
                html = html.replace('<strong>', '<b>').replace('</strong>', '</b>')
                html = html.replace('<em>', '<i>').replace('</em>', '</i>')
                html = html.replace('<b>', '<b>').replace('</b>', '</b>')  # Уже правильный
                html = html.replace('<i>', '<i>').replace('</i>', '</i>')  # Уже правильный
                
                # Конвертируем заголовки в жирный текст
                html = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'<b>\1</b>', html)
                
                # Конвертируем списки в простой текст с маркерами
                html = re.sub(r'<ul[^>]*>', '', html)
                html = re.sub(r'</ul>', '', html)
                html = re.sub(r'<ol[^>]*>', '', html)
                html = re.sub(r'</ol>', '', html)
                html = re.sub(r'<li[^>]*>', '• ', html)
                html = re.sub(r'</li>', '\n', html)
                
                # Конвертируем параграфы в простой текст
                html = re.sub(r'<p[^>]*>', '', html)
                html = re.sub(r'</p>', '\n\n', html)
                
                # Убираем лишние переносы строк
                html = re.sub(r'\n{3,}', '\n\n', html)
                html = html.strip()
                
                # Экранируем HTML символы для безопасного использования в Telegram
                html = TelegramFormatter.escape_html(html)
                
                # Восстанавливаем теги форматирования, которые поддерживает Telegram
                allowed_tags = ['b', 'i', 'u', 's', 'a', 'code', 'pre']
                for tag in allowed_tags:
                    html = html.replace(f'&lt;{tag}&gt;', f'<{tag}>')
                    html = html.replace(f'&lt;/{tag}&gt;', f'</{tag}>')
                
                # Восстанавливаем атрибуты для ссылок
                html = html.replace('&lt;a href=', '<a href=')
                html = html.replace('&gt;', '>')
            
            return html
            
        except ImportError:
            logger.warning("Библиотека markdown не установлена, используем fallback")
            return TelegramFormatter._markdown_to_html_fallback(markdown_text)
        except Exception as e:
            logger.error(f"Ошибка преобразования Markdown в HTML: {e}")
            return TelegramFormatter._markdown_to_html_fallback(markdown_text)
    
    @staticmethod
    def _markdown_to_html_fallback(markdown_text: str) -> str:
        """
        Fallback функция для преобразования Markdown в HTML без внешних библиотек
        Обрабатывает только основные элементы
        """
        html = markdown_text
        
        # Заголовки - конвертируем в жирный текст для Telegram
        html = re.sub(r'^### (.*?)$', r'<b>\1</b>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<b>\1</b>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<b>\1</b>', html, flags=re.MULTILINE)
        
        # Жирный и курсивный текст
        html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', html)
        html = re.sub(r'\*(.*?)\*', r'<i>\1</i>', html)
        
        # Списки
        html = re.sub(r'^- (.*?)$', r'• \1', html, flags=re.MULTILINE)
        
        # Код
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Экранируем HTML символы
        html = TelegramFormatter.escape_html(html)
        
        # Восстанавливаем теги форматирования
        html = html.replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
        html = html.replace('&lt;i&gt;', '<i>').replace('&lt;/i&gt;', '</i>')
        html = html.replace('&lt;code&gt;', '<code>').replace('&lt;/code&gt;', '</code>')
        
        return html
    
    @staticmethod
    def remove_markdown_formatting(text: str) -> str:
        """
        Удаляет все markdown форматирование из текста, оставляя только обычный текст
        
        Args:
            text: Текст с markdown форматированием
            
        Returns:
            Обычный текст без форматирования
        """
        if not text:
            return text
        
        import re
        
        # Удаляем markdown форматирование
        # Жирный текст: **text** или __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Курсив: *text* или _text_
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Код: `text`
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Блоки кода: ```text```
        text = re.sub(r'```.*?\n(.*?)\n```', r'\1', text, flags=re.DOTALL)
        
        # Ссылки: [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Заголовки: # text
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        
        # Списки: - text или * text
        text = re.sub(r'^[\s]*[-*+]\s*', '', text, flags=re.MULTILINE)
        
        # Блоки цитат: > text
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
        
        # Убираем лишние пробелы и переносы строк
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text