from telegram import Update
from telegram.ext import ContextTypes
from .service import SummaryService
from .models import SummaryType
from shared.utils import format_success_message, format_error_message, format_date_for_display
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class SummaryHandlers:
    """Обработчики для работы с суммаризациями"""
    
    def __init__(self, summary_service: SummaryService):
        self.summary_service = summary_service
    
    async def check_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик проверки суммаризации"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.split('_')[-1]
            
            available_summaries = self.summary_service.get_available_summaries(vk_chat_id)
            
            if not available_summaries:
                await query.edit_message_text(
                    "📋 Нет доступных суммаризаций\n\n"
                    "Сначала выполните анализ чата."
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.date_selection_keyboard(available_summaries)
            
            summary_list_text = "📋 Доступные суммаризации:\n\n"
            for summary in available_summaries[:5]:
                date_display = format_date_for_display(summary.date)
                summary_list_text += f"📅 {date_display}\n"
            
            await query.edit_message_text(
                summary_list_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в check_summary_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_date_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора даты"""
        query = update.callback_query
        await query.answer()
        
        try:
            date = query.data.split('_')[-1]
            context.user_data['selected_date'] = date
            
            vk_chat_id = context.user_data.get('selected_chat_id')
            if not vk_chat_id:
                await query.edit_message_text(
                    "❌ Чат не выбран"
                )
                return
            
            summary = self.summary_service.get_summary(vk_chat_id, date, SummaryType.DAILY)
            
            if not summary:
                await query.edit_message_text(
                    f"❌ Суммаризация за {format_date_for_display(date)} не найдена"
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            summary_text = summary.summary_text
            if len(summary_text) > 1000:
                summary_text = summary_text[:1000] + "..."
            
            await query.edit_message_text(
                f"📋 Суммаризация за {format_date_for_display(date)}\n\n"
                f"{summary_text}",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_date_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации суммаризации в группу"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.split('_')[-1]
            group_id = context.user_data.get('selected_group_id')
            
            if not group_id:
                await query.edit_message_text(
                    "❌ Группа не выбрана"
                )
                return
            
            available_summaries = self.summary_service.get_available_summaries(vk_chat_id)
            
            if not available_summaries:
                await query.edit_message_text(
                    "❌ Нет суммаризаций для публикации"
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.date_selection_keyboard(available_summaries)
            
            await query.edit_message_text(
                "📤 Публикация суммаризации\n\n"
                "Выберите дату для публикации:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_summary_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_summary_html_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации суммаризации в HTML формате"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.split('_')[-1]
            group_id = context.user_data.get('selected_group_id')
            
            if not group_id:
                await query.edit_message_text(
                    "❌ Группа не выбрана"
                )
                return
            
            available_summaries = self.summary_service.get_available_summaries(vk_chat_id)
            
            if not available_summaries:
                await query.edit_message_text(
                    "❌ Нет суммаризаций для публикации"
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.date_selection_keyboard(available_summaries)
            
            await query.edit_message_text(
                "📤 Публикация суммаризации (HTML)\n\n"
                "Выберите дату для публикации:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_summary_html_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_to_group_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации в группу"""
        query = update.callback_query
        await query.answer()
        
        try:
            date = context.user_data.get('selected_date')
            vk_chat_id = context.user_data.get('selected_chat_id')
            group_id = context.user_data.get('selected_group_id')
            use_html = context.user_data.get('use_html_format', False)
            
            if not all([date, vk_chat_id, group_id]):
                await query.edit_message_text(
                    "❌ Не все параметры выбраны"
                )
                return
            
            summary = self.summary_service.get_summary(vk_chat_id, date, SummaryType.DAILY)
            
            logger.info(f"DEBUG: summary type = {type(summary)}, summary = {summary}")
            
            if not summary:
                await query.edit_message_text(
                    f"❌ Суммаризация за {format_date_for_display(date)} не найдена"
                )
                return
            
            from infrastructure.telegram import sender
            from infrastructure.telegram import formatter
            from shared.utils import format_summary_for_telegram_html_universal
            
            if use_html:
                formatted_parts = format_summary_for_telegram_html_universal(
                    summary.summary_text, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = 'HTML'
            else:
                from shared.utils import format_summary_for_telegram
                formatted_parts = format_summary_for_telegram(
                    summary.summary_text, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = 'MarkdownV2'
            
            for part in formatted_parts:
                await sender.TelegramMessageSender.safe_send_message(
                    context.bot,
                    group_id,
                    part,
                    parse_mode=parse_mode
                )
            
            await query.edit_message_text(
                format_success_message(
                    f"Суммаризация опубликована в группу"
                )
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_to_group_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )

