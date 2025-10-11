"""
Универсальная система отправки сообщений в Telegram с автоматическим экранированием
"""
import logging
from typing import Optional, Union, List
from telegram import Update, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from telegram_formatter import TelegramFormatter
# from utils import escape_markdown_v2 as escape_md_preserve_formatting  # Не используется

logger = logging.getLogger(__name__)

class TelegramMessageSender:
    """
    Универсальный класс для безопасной отправки сообщений в Telegram
    с автоматическим экранированием и fallback системой
    """
    
    @staticmethod
    async def safe_edit_message_text(
        query: CallbackQuery,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2
    ) -> bool:
        """
        Безопасно редактирует сообщение с MarkdownV2 форматированием
        
        Args:
            query: CallbackQuery объект
            text: Текст сообщения
            reply_markup: Клавиатура (опционально)
            parse_mode: Режим парсинга (по умолчанию MARKDOWN_V2)
        
        Returns:
            True если сообщение отправлено успешно, False иначе
        """
        logger.debug("=== SAFE_EDIT_MESSAGE_TEXT START ===")
        logger.debug(f"Original text:\n{text}")
        
        # Escape reserved characters for MarkdownV2
        markdown_text = TelegramMessageSender.escape_reserved_chars_for_markdown_v2(text)
        logger.debug(f"Escaped text:\n{markdown_text}")
        
        try:
            await query.edit_message_text(
                text=markdown_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.debug("✅ Message edited successfully with MARKDOWN_V2")
            return True
            
        except Exception as e:
            logger.error(f"❌ MARKDOWN_V2 parsing failed: {e}")
            logger.error(f"Failed text:\n{markdown_text}")
            
            # Анализируем проблемные символы
            logger.error("=== ANALYZING PROBLEMATIC CHARACTERS ===")
            reserved_chars = ['-', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '=', '|', '{', '}', '.', '!']
            for char in reserved_chars:
                count = markdown_text.count(char)
                if count > 0:
                    logger.error(f"Character '{char}' appears {count} times")
                    # Показываем первые несколько вхождений
                    pos = 0
                    shown = 0
                    while pos != -1 and shown < 3:
                        pos = markdown_text.find(char, pos)
                        if pos != -1:
                            start = max(0, pos - 20)
                            end = min(len(markdown_text), pos + 20)
                            context = markdown_text[start:end]
                            logger.error(f"  Position {pos}: ...{context}...")
                            pos += 1
                            shown += 1
            
            raise e
    
    # Старые функции удалены - теперь используем escape_reserved_chars_for_markdown_v2
    
    @staticmethod
    def format_text_for_html(text: str) -> str:
        """
        Форматирует текст для безопасного использования в HTML
        
        Args:
            text: Исходный текст
            
        Returns:
            Экранированный текст
        """
        return TelegramFormatter.escape_html(text)
    
    @staticmethod
    def create_bold_text(text: str) -> str:
        """
        Создает жирный текст для MarkdownV2
        
        Args:
            text: Исходный текст
            
        Returns:
            Жирный текст
        """
        return TelegramFormatter.format_bold(text)
    
    @staticmethod
    def create_italic_text(text: str) -> str:
        """
        Создает курсивный текст для MarkdownV2
        
        Args:
            text: Исходный текст
            
        Returns:
            Курсивный текст
        """
        return TelegramFormatter.format_italic(text)
    
    @staticmethod
    def create_list_item(text: str, level: int = 0) -> str:
        """
        Создает элемент списка для MarkdownV2
        
        Args:
            text: Текст элемента
            level: Уровень вложенности
            
        Returns:
            Элемент списка
        """
        return TelegramFormatter.format_list_item(text, level)
    
    @staticmethod
    def validate_markdown_v2(text: str) -> bool:
        """
        Валидирует MarkdownV2 текст
        
        Args:
            text: Текст для валидации
            
        Returns:
            True если текст валиден, False иначе
        """
        return TelegramFormatter.validate_markdown_v2(text)
    
    @staticmethod
    def split_long_message(text: str, max_length: int = 4096) -> List[str]:
        """
        Разбивает длинное сообщение на части
        
        Args:
            text: Исходный текст
            max_length: Максимальная длина части
            
        Returns:
            Список частей сообщения
        """
        return TelegramFormatter.split_message(text, max_length)
    
    @staticmethod
    def auto_format_text(text: str, parse_mode: ParseMode = ParseMode.MARKDOWN_V2) -> str:
        """
        Автоматически форматирует текст для указанного режима парсинга
        
        Args:
            text: Исходный текст
            parse_mode: Режим парсинга
            
        Returns:
            Отформатированный текст
        """
        if parse_mode == ParseMode.MARKDOWN_V2:
            return TelegramMessageSender.format_text_for_markdown_v2(text)
        elif parse_mode == ParseMode.HTML:
            return TelegramMessageSender.format_text_for_html(text)
        else:
            return text

    @staticmethod
    def escape_reserved_chars_for_markdown_v2(text: str) -> str:
        """
        Smart escaping for MarkdownV2 - escape reserved characters with special handling for dots.
        
        Args:
            text: The input text to escape.
        
        Returns:
            Text with reserved characters escaped.
        """
        logger.debug("=== ESCAPE_RESERVED_CHARS_FOR_MARKDOWN_V2 START ===")
        logger.debug(f"Input text:\n{text}")
        
        # MarkdownV2 reserved characters that need escaping
        reserved_chars = ['-', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '=', '|', '{', '}', '!']
        
        # Escape all reserved characters except dots
        escaped_text = text
        for char in reserved_chars:
            if char in escaped_text:
                old_text = escaped_text
                escaped_text = escaped_text.replace(char, f'\\{char}')
                count = old_text.count(char)
                logger.debug(f"Escaped '{char}' {count} times")
        
        # Special handling for dots - escape all dots to be safe
        import re
        
        # Escape all dots - it's safer to escape all of them
        escaped_text = escaped_text.replace('.', '\\.')
        
        logger.debug(f"Final result:\n{escaped_text}")
        logger.debug("=== ESCAPE_RESERVED_CHARS_FOR_MARKDOWN_V2 END ===")
        return escaped_text

    @staticmethod
    def convert_markdown_to_html(text: str) -> str:
        """
        Converts Markdown formatted text to HTML.
        
        Args:
            text: The input text with Markdown formatting.
        
        Returns:
            Text converted to HTML formatting.
        """
        # Convert *bold* to <b>bold</b>
        import re
        html_text = re.sub(r'\*([^\*]+)\*', r'<b>\1</b>', text)
        # Escape special HTML characters if needed
        html_text = TelegramFormatter.escape_html(html_text)
        return html_text
