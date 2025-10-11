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
