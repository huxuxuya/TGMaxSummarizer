"""
Универсальная система отправки сообщений в Telegram с автоматическим экранированием
"""
import logging
from typing import Optional, Union, List
from telegram import Update, InlineKeyboardMarkup, CallbackQuery
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from .formatter import TelegramFormatter, TextContentType
from ..logging.message_logger import TelegramMessageLogger
import telegramify_markdown
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
        content_type: TextContentType = TextContentType.FORMATTED,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2
    ) -> bool:
        """
        Безопасно редактирует сообщение с MarkdownV2 форматированием
        
        Args:
            query: CallbackQuery объект
            text: Текст сообщения
            content_type: Тип контента (RAW, FORMATTED, TECHNICAL). По умолчанию FORMATTED
                для обратной совместимости с существующим кодом
            reply_markup: Клавиатура (опционально)
            parse_mode: Режим парсинга (по умолчанию MARKDOWN_V2)
        
        Returns:
            True если сообщение отправлено успешно, False иначе
        """
        logger.debug("=== SAFE_EDIT_MESSAGE_TEXT START ===")
        logger.debug(f"Original text:\n{text}")
        logger.debug(f"Content type: {content_type}")
        
        # Выбираем метод экранирования в зависимости от parse_mode и content_type
        if parse_mode == ParseMode.MARKDOWN_V2:
            # Обработка MarkdownV2
            if content_type == TextContentType.RAW:
                # Сырой текст - используем встроенный хелпер telegram
                formatted_text = escape_markdown(text, version=2)
                logger.debug("Using telegram.helpers.escape_markdown() for RAW content")
            elif content_type == TextContentType.FORMATTED:
                # Форматированный текст - используем наш умный эскейпер
                formatted_text = TelegramFormatter.smart_escape_markdown_v2(text)
                logger.debug("Using TelegramFormatter.smart_escape_markdown_v2() for FORMATTED content")
            elif content_type == TextContentType.TECHNICAL:
                # Технический текст - оборачиваем в код
                formatted_text = f"`{text}`"
                logger.debug("Wrapping in backticks for TECHNICAL content")
            elif content_type == TextContentType.STANDARD_MARKDOWN:
                # Стандартный Markdown - конвертируем через telegramify-markdown
                formatted_text = TelegramMessageSender.convert_standard_markdown_to_telegram(text)
                logger.debug("Using telegramify-markdown for STANDARD_MARKDOWN content")
            elif content_type == TextContentType.HTML:
                # HTML - конвертируем в Telegram MarkdownV2
                formatted_text = TelegramMessageSender.convert_html_to_telegram_markdown(text)
                logger.debug("Converting HTML to Telegram MarkdownV2")
            else:
                # Fallback на FORMATTED
                formatted_text = TelegramFormatter.smart_escape_markdown_v2(text)
                logger.warning(f"Unknown content type {content_type}, using FORMATTED as fallback")
            
            logger.debug(f"Text for MarkdownV2:\n{formatted_text}")
            
        elif parse_mode == ParseMode.HTML:
            # Обработка HTML
            if content_type == TextContentType.RAW:
                # Сырой текст - экранируем HTML для безопасности
                formatted_text = TelegramFormatter.escape_html(text)
                logger.debug("Using TelegramFormatter.escape_html() for RAW content")
            elif content_type == TextContentType.FORMATTED:
                # Форматированный текст - уже содержит валидный HTML, не трогаем
                formatted_text = text
                logger.debug("Using text as-is for FORMATTED HTML content")
            elif content_type == TextContentType.TECHNICAL:
                # Технический текст - оборачиваем в <code>
                formatted_text = f"<code>{TelegramFormatter.escape_html(text)}</code>"
                logger.debug("Wrapping in <code> tags for TECHNICAL content")
            else:
                # Fallback - экранируем для безопасности
                formatted_text = TelegramFormatter.escape_html(text)
                logger.warning(f"Unknown content type {content_type}, using RAW as fallback")
            
            logger.debug(f"Text for HTML:\n{formatted_text}")
            
        else:
            # Для других режимов парсинга используем текст как есть
            formatted_text = text
            logger.debug(f"Using text as-is for parse_mode: {parse_mode}")
        
        # Создаем метаданные для логирования
        metadata = TelegramMessageLogger.create_metadata(
            chat_id=query.message.chat_id if query.message else None,
            action="edit",
            parse_mode=parse_mode.value if parse_mode else "None",
            content_type=content_type.value,
            original_text=text,
            formatted_text=formatted_text
        )
        
        # Логируем сообщение перед отправкой
        log_path = TelegramMessageLogger.log_message(metadata)
        
        try:
            await query.edit_message_text(
                text=formatted_text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            logger.debug(f"✅ Message edited successfully with {parse_mode}")
            
            # Обновляем лог при успехе
            TelegramMessageLogger.log_success(log_path, query.message.message_id if query.message else None)
            return True
            
        except Exception as e:
            logger.error(f"❌ Message editing failed: {e}")
            logger.error(f"Failed text:\n{formatted_text}")
            
            # Обновляем лог при ошибке
            TelegramMessageLogger.log_error(log_path, str(e))
            raise e
    
    # Старые функции удалены - теперь используем smart_escape_markdown_v2 из TelegramFormatter
    
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
            return TelegramFormatter.escape_markdown_v2(text)
        elif parse_mode == ParseMode.HTML:
            return TelegramMessageSender.format_text_for_html(text)
        else:
            return text
    
    @staticmethod
    def convert_standard_markdown_to_telegram(markdown_text: str) -> str:
        """
        Конвертирует стандартный Markdown в Telegram MarkdownV2 используя telegramify-markdown
        
        Args:
            markdown_text: Текст в стандартном Markdown формате
            
        Returns:
            Текст в формате Telegram MarkdownV2
        """
        try:
            # Используем telegramify-markdown для конвертации
            telegram_text = telegramify_markdown.markdownify(markdown_text)
            logger.debug(f"✅ Successfully converted markdown to telegram format")
            logger.debug(f"Original: {markdown_text[:100]}...")
            logger.debug(f"Converted: {telegram_text[:100]}...")
            
            # Дополнительная валидация результата
            TelegramMessageSender._validate_telegram_markdown(telegram_text, markdown_text)
            
            return telegram_text
        except Exception as e:
            logger.error(f"❌ Failed to convert markdown with telegramify-markdown: {e}")
            logger.error(f"Problematic text preview: {markdown_text[:200]}...")
            
            # Детальное логирование проблемных символов
            TelegramMessageSender._log_problematic_characters(markdown_text)
            
            # Fallback на наш собственный метод
            logger.debug("🔄 Using fallback conversion method")
            return TelegramFormatter.smart_escape_markdown_v2(markdown_text)
    
    @staticmethod
    def _validate_telegram_markdown(telegram_text: str, original_text: str) -> None:
        """
        Валидирует результат конвертации в Telegram MarkdownV2
        
        Args:
            telegram_text: Конвертированный текст
            original_text: Исходный текст
        """
        # Проверяем на незакрытые теги bold
        asterisk_count = telegram_text.count('*')
        if asterisk_count % 2 != 0:
            logger.warning(f"⚠️ UNBALANCED BOLD TAGS: {asterisk_count} asterisks (should be even)")
            logger.warning(f"Problematic text: {telegram_text[:200]}...")
        
        # Проверяем на незакрытые теги italic
        underscore_count = telegram_text.count('_')
        if underscore_count % 2 != 0:
            logger.warning(f"⚠️ UNBALANCED ITALIC TAGS: {underscore_count} underscores (should be even)")
            logger.warning(f"Problematic text: {telegram_text[:200]}...")
        
        # Проверяем на незакрытые теги code
        backtick_count = telegram_text.count('`')
        if backtick_count % 2 != 0:
            logger.warning(f"⚠️ UNBALANCED CODE TAGS: {backtick_count} backticks (should be even)")
            logger.warning(f"Problematic text: {telegram_text[:200]}...")
    
    @staticmethod
    def _log_problematic_characters(text: str) -> None:
        """
        Логирует проблемные символы в тексте
        
        Args:
            text: Текст для анализа
        """
        # Символы, которые могут вызывать проблемы в MarkdownV2
        problematic_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        logger.debug("=== PROBLEMATIC CHARACTERS ANALYSIS ===")
        for char in problematic_chars:
            count = text.count(char)
            if count > 0:
                logger.debug(f"Char '{char}': {count} occurrences")
                
                # Находим позиции проблемных символов
                positions = []
                for i, c in enumerate(text):
                    if c == char:
                        positions.append(i)
                        if len(positions) >= 5:  # Ограничиваем количество позиций
                            positions.append("...")
                            break
                
                if positions:
                    logger.debug(f"  Positions: {positions}")
        
        # Анализ списков с маркерами
        lines = text.split('\n')
        list_markers = ['* ', '- ', '+ ', '1. ', '2. ', '3. ']
        for i, line in enumerate(lines):
            for marker in list_markers:
                if line.strip().startswith(marker):
                    logger.debug(f"List item at line {i+1}: '{line.strip()}'")
                    break
        
        logger.debug("=== END PROBLEMATIC CHARACTERS ANALYSIS ===")
    
    @staticmethod
    def convert_html_to_telegram_markdown(html_text: str) -> str:
        """
        Конвертирует HTML в Telegram MarkdownV2
        
        Args:
            html_text: Текст в HTML формате
            
        Returns:
            Текст в формате Telegram MarkdownV2
        """
        try:
            # Сначала конвертируем HTML в стандартный Markdown
            import markdown
            from markdown.extensions import Extension
            
            # Создаем простой HTML to Markdown конвертер
            # Это базовая реализация, можно расширить
            markdown_text = html_text
            
            # Простые замены HTML тегов на Markdown
            replacements = [
                (r'<b>(.*?)</b>', r'**\1**'),
                (r'<strong>(.*?)</strong>', r'**\1**'),
                (r'<i>(.*?)</i>', r'*\1*'),
                (r'<em>(.*?)</em>', r'*\1*'),
                (r'<code>(.*?)</code>', r'`\1`'),
                (r'<pre>(.*?)</pre>', r'```\n\1\n```'),
                (r'<h1>(.*?)</h1>', r'# \1'),
                (r'<h2>(.*?)</h2>', r'## \1'),
                (r'<h3>(.*?)</h3>', r'### \1'),
                (r'<a href="([^"]*)">(.*?)</a>', r'[\2](\1)'),
            ]
            
            import re
            for pattern, replacement in replacements:
                markdown_text = re.sub(pattern, replacement, markdown_text, flags=re.DOTALL)
            
            # Теперь конвертируем в Telegram MarkdownV2
            return TelegramMessageSender.convert_standard_markdown_to_telegram(markdown_text)
            
        except Exception as e:
            logger.error(f"❌ Failed to convert HTML to telegram markdown: {e}")
            # Fallback - просто экранируем HTML
            return TelegramFormatter.escape_html(html_text)


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
    
    @staticmethod
    async def safe_send_message(
        bot,
        chat_id: Union[int, str],
        text: str,
        content_type: TextContentType = TextContentType.FORMATTED,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: ParseMode = ParseMode.MARKDOWN_V2,
        disable_notification: bool = False,
        disable_web_page_preview: bool = True,
        **kwargs
    ) -> bool:
        """
        Безопасно отправляет сообщение с автоматическим экранированием
        
        Args:
            bot: Bot объект
            chat_id: ID чата
            text: Текст сообщения
            content_type: Тип контента (RAW, FORMATTED, TECHNICAL). По умолчанию FORMATTED
            reply_markup: Клавиатура (опционально)
            parse_mode: Режим парсинга (по умолчанию MARKDOWN_V2)
            disable_notification: Отключить уведомления
            disable_web_page_preview: Отключить превью ссылок
            **kwargs: Дополнительные параметры для send_message
        
        Returns:
            True если сообщение отправлено успешно, False иначе
        """
        logger.debug("=== SAFE_SEND_MESSAGE START ===")
        logger.debug(f"Original text:\n{text}")
        logger.debug(f"Content type: {content_type}")
        
        # Подготавливаем formatted_text в зависимости от parse_mode
        formatted_text = text  # По умолчанию
        
        if parse_mode == ParseMode.MARKDOWN_V2:
            # Выбираем метод экранирования в зависимости от типа контента
            if content_type == TextContentType.RAW:
                formatted_text = escape_markdown(text, version=2)
                logger.debug("Using telegram.helpers.escape_markdown() for RAW content")
            elif content_type == TextContentType.FORMATTED:
                formatted_text = TelegramFormatter.smart_escape_markdown_v2(text)
                logger.debug("Using TelegramFormatter.smart_escape_markdown_v2() for FORMATTED content")
            elif content_type == TextContentType.TECHNICAL:
                formatted_text = f"`{text}`"
                logger.debug("Wrapping in backticks for TECHNICAL content")
            elif content_type == TextContentType.STANDARD_MARKDOWN:
                # Стандартный Markdown - конвертируем через telegramify-markdown
                formatted_text = TelegramMessageSender.convert_standard_markdown_to_telegram(text)
                logger.debug("Using telegramify-markdown for STANDARD_MARKDOWN content")
            elif content_type == TextContentType.HTML:
                # HTML - конвертируем в Telegram MarkdownV2
                formatted_text = TelegramMessageSender.convert_html_to_telegram_markdown(text)
                logger.debug("Converting HTML to Telegram MarkdownV2")
            else:
                formatted_text = TelegramFormatter.smart_escape_markdown_v2(text)
                logger.warning(f"Unknown content type {content_type}, using FORMATTED as fallback")
            
            logger.debug(f"Text for MarkdownV2:\n{formatted_text}")
            
            # Дополнительная отладка для поиска проблемных символов
            logger.debug("=== SEND_MESSAGE MARKDOWN_V2 DEBUG INFO ===")
            logger.debug(f"Original text length: {len(text)}")
            logger.debug(f"Formatted text length: {len(formatted_text)}")
            logger.debug(f"Content type: {content_type}")
            
            # Проверяем на проблемные символы
            problematic_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in problematic_chars:
                count_orig = text.count(char)
                count_formatted = formatted_text.count(char)
                if count_orig > 0 or count_formatted > 0:
                    logger.debug(f"Char '{char}': original={count_orig}, formatted={count_formatted}")
            
            # Проверяем на незакрытые теги
            bold_count = formatted_text.count('*')
            if bold_count % 2 != 0:
                logger.warning(f"⚠️ UNBALANCED BOLD TAGS: {bold_count} asterisks (should be even)")
            
            logger.debug("=== END SEND_MESSAGE MARKDOWN_V2 DEBUG ===")
            
        elif parse_mode == ParseMode.HTML:
            # Выбираем обработку в зависимости от типа контента
            if content_type == TextContentType.RAW:
                # Сырой текст - экранируем HTML для безопасности
                formatted_text = TelegramFormatter.escape_html(text)
                logger.debug("Using TelegramFormatter.escape_html() for RAW content")
            elif content_type == TextContentType.FORMATTED:
                # Форматированный текст - уже содержит валидный HTML, не трогаем
                formatted_text = text
                logger.debug("Using text as-is for FORMATTED HTML content")
            elif content_type == TextContentType.TECHNICAL:
                # Технический текст - оборачиваем в <code>
                formatted_text = f"<code>{TelegramFormatter.escape_html(text)}</code>"
                logger.debug("Wrapping in <code> tags for TECHNICAL content")
            else:
                # Fallback - экранируем для безопасности
                formatted_text = TelegramFormatter.escape_html(text)
                logger.warning(f"Unknown content type {content_type}, using RAW as fallback")
            
            logger.debug(f"Text for HTML:\n{formatted_text}")
        
        # Создаем метаданные для логирования
        metadata = TelegramMessageLogger.create_metadata(
            chat_id=chat_id,
            action="send",
            parse_mode=parse_mode.value if parse_mode else "None",
            content_type=content_type.value,
            original_text=text,
            formatted_text=formatted_text
        )
        
        # Логируем сообщение перед отправкой
        log_path = TelegramMessageLogger.log_message(metadata)
        
        try:
            if parse_mode == ParseMode.MARKDOWN_V2:
                message = await bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_notification=disable_notification,
                    disable_web_page_preview=disable_web_page_preview,
                    **kwargs
                )
            elif parse_mode == ParseMode.HTML:
                message = await bot.send_message(
                    chat_id=chat_id,
                    text=formatted_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                    disable_notification=disable_notification,
                    disable_web_page_preview=disable_web_page_preview,
                    **kwargs
                )
            else:
                # Для обычного текста без форматирования
                message = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=None,
                    disable_notification=disable_notification,
                    disable_web_page_preview=disable_web_page_preview,
                    **kwargs
                )
            
            logger.debug("✅ Message sent successfully")
            
            # Обновляем лог при успехе
            TelegramMessageLogger.log_success(log_path, message.message_id if message else None)
            return True
            
        except Exception as e:
            logger.error(f"❌ SEND_MESSAGE parsing failed: {e}")
            logger.error(f"Failed text:\n{text}")
            
            # Обновляем лог при ошибке
            TelegramMessageLogger.log_error(log_path, str(e))
            
            # Fallback: отправляем как обычный текст
            try:
                logger.debug("🔄 Fallback: sending as plain text")
                
                # Создаем новый лог для fallback попытки
                fallback_metadata = TelegramMessageLogger.create_metadata(
                    chat_id=chat_id,
                    action="send_fallback",
                    parse_mode="None",
                    content_type="RAW",
                    original_text=text,
                    formatted_text=text
                )
                fallback_log_path = TelegramMessageLogger.log_message(fallback_metadata)
                
                message = await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=None,
                    disable_notification=disable_notification,
                    disable_web_page_preview=disable_web_page_preview,
                    **kwargs
                )
                logger.debug("✅ Fallback message sent successfully")
                
                # Обновляем лог fallback при успехе
                TelegramMessageLogger.log_success(fallback_log_path, message.message_id if message else None)
                return True
                
            except Exception as fallback_error:
                logger.error(f"❌ Fallback also failed: {fallback_error}")
                
                # Обновляем лог fallback при ошибке
                TelegramMessageLogger.log_error(fallback_log_path, str(fallback_error))
                return False