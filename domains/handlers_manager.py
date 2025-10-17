from telegram import Update
from telegram.ext import ContextTypes
from .users.handlers import UserHandlers
from .chats.handlers import ChatHandlers
from .ai.handlers import AIHandlers
from .summaries.handlers import SummaryHandlers
from .users.service import UserService
from .chats.service import ChatService
from .ai.service import AIService
from .summaries.service import SummaryService
from core.database.connection import DatabaseConnection
from core.config import load_config
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class HandlersManager:
    """Менеджер всех обработчиков бота"""
    
    def __init__(self):
        config = load_config()
        db_connection = DatabaseConnection(config['database'].path)
        
        self.user_service = UserService(db_connection)
        self.chat_service = ChatService(db_connection)
        self.summary_service = SummaryService(db_connection)
        
        from infrastructure.ai_providers.factory import ProviderFactory
        provider_factory = ProviderFactory()
        self.ai_service = AIService(db_connection, provider_factory, config['ai'].providers)
        
        self.user_handlers = UserHandlers(self.user_service)
        self.chat_handlers = ChatHandlers(self.chat_service)
        self.ai_handlers = AIHandlers(self.ai_service)
        self.summary_handlers = SummaryHandlers(self.summary_service)
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главный обработчик /start"""
        await self.user_handlers.start_handler(update, context)
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        data = query.data
        
        try:
            if data == CallbackActions.MANAGE_CHATS:
                await self.chat_handlers.manage_chats_handler(update, context)
            elif data == CallbackActions.ADD_CHAT:
                await self.chat_handlers.add_chat_handler(update, context)
            elif data == CallbackActions.LIST_CHATS:
                await self.chat_handlers.list_chats_handler(update, context)
            elif data == CallbackActions.REMOVE_CHAT:
                await self.chat_handlers.remove_chat_handler(update, context)
            elif data == CallbackActions.SELECT_AI_PROVIDER:
                await self.ai_handlers.select_ai_provider_handler(update, context)
            elif data == CallbackActions.CHANGE_GROUP:
                await self.user_handlers.change_group_handler(update, context)
            elif data.startswith("select_group_"):
                await self.user_handlers.select_group_handler(update, context)
            elif data.startswith("select_provider:"):
                await self.ai_handlers.select_provider_handler(update, context)
            elif data.startswith("confirm_provider:"):
                await self.ai_handlers.confirm_provider_handler(update, context)
            elif data.startswith("chat_settings_"):
                await self.chat_handlers.chat_settings_handler(update, context)
            elif data.startswith("chat_stats_"):
                await self.chat_handlers.chat_stats_handler(update, context)
            elif data.startswith("load_messages_"):
                await self.chat_handlers.load_messages_handler(update, context)
            elif data.startswith("load_new_messages_"):
                chat_id = data.split("_")[3]
                await self.chat_handlers._load_messages_worker(update, context, chat_id, load_only_new=True)
            elif data.startswith("load_all_messages_"):
                chat_id = data.split("_")[3]
                await self.chat_handlers._load_messages_worker(update, context, chat_id, load_only_new=False)
            elif data.startswith("select_chat_"):
                await self.chat_handlers.select_chat_handler(update, context)
            elif data.startswith("check_summary_"):
                await self.summary_handlers.check_summary_handler(update, context)
            elif data.startswith("publish_summary_"):
                await self.summary_handlers.publish_summary_handler(update, context)
            elif data.startswith("publish_summary_html_"):
                await self.summary_handlers.publish_summary_html_handler(update, context)
            elif data.startswith("select_date_"):
                await self.summary_handlers.select_date_handler(update, context)
            elif data == "select_model_for_analysis":
                await self.ai_handlers.select_model_for_analysis_handler(update, context)
            elif data == CallbackActions.CANCEL:
                await self._handle_cancel(update, context)
            elif data == CallbackActions.BACK_TO_MAIN:
                await self._handle_back_to_main(update, context)
            elif data == CallbackActions.BACK_TO_MANAGE_CHATS:
                await self._handle_back_to_manage_chats(update, context)
            elif data == CallbackActions.BACK_TO_CHAT_SETTINGS:
                await self._handle_back_to_chat_settings(update, context)
            elif data == "back_to_chat_management":
                await self._handle_back_to_chat_management(update, context)
            elif data == "ai_provider_settings":
                await self.ai_handlers.ai_provider_settings_handler(update, context)
            elif data == "ai_provider_defaults":
                await self.ai_handlers.ai_provider_defaults_handler(update, context)
            elif data == "ai_provider_status":
                await self.ai_handlers.ai_provider_status_handler(update, context)
            elif data == "check_providers_availability":
                await self.ai_handlers.check_providers_availability_handler(update, context)
            elif data == "openrouter_model_selection":
                await self.ai_handlers.openrouter_model_selection_handler(update, context)
            elif data == "top5_models_selection":
                await self.ai_handlers.top5_models_selection_handler(update, context)
            elif data.startswith("select_openrouter_model:"):
                await self.ai_handlers.select_openrouter_model_handler(update, context)
            elif data.startswith("confirm_openrouter_model:"):
                await self.ai_handlers.confirm_openrouter_model_handler(update, context)
            elif data.startswith("select_top5_model:"):
                await self.ai_handlers.select_top5_model_handler(update, context)
            elif data.startswith("confirm_top5_model:"):
                await self.ai_handlers.confirm_top5_model_handler(update, context)
            elif data.startswith("select_ollama_model:"):
                await self.ai_handlers.select_ollama_model_handler(update, context)
            elif data.startswith("analyze_with_provider:"):
                await self.ai_handlers.analyze_with_provider_handler(update, context)
            else:
                await query.answer("Неизвестная команда")
                
        except Exception as e:
            logger.error(f"Ошибка в callback_query_handler: {e}")
            await query.answer("Произошла ошибка")
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        message = update.effective_message
        
        if message.text.startswith('/'):
            await message.reply_text(
                "Используйте кнопки для навигации по боту."
            )
        else:
            await message.reply_text(
                "Я понимаю только команды. Используйте /start для начала работы."
            )
    
    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        message = update.effective_message
        
        if message.caption and "расписание" in message.caption.lower():
            await self._handle_schedule_photo(update, context)
        else:
            await message.reply_text(
                "Фотография получена. Если это расписание, добавьте подпись 'расписание'."
            )
    
    async def _handle_schedule_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фото расписания"""
        try:
            group_id = update.effective_chat.id
            file_id = update.effective_message.photo[-1].file_id
            
            success = self.chat_service.set_schedule_photo(group_id, file_id)
            
            if success:
                await update.effective_message.reply_text(
                    "✅ Фото расписания сохранено"
                )
            else:
                await update.effective_message.reply_text(
                    "❌ Не удалось сохранить фото расписания"
                )
                
        except Exception as e:
            logger.error(f"Ошибка в _handle_schedule_photo: {e}")
            await update.effective_message.reply_text(
                "❌ Ошибка при сохранении фото расписания"
            )
    
    async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик отмены"""
        query = update.callback_query
        await query.answer()
        
        from infrastructure.telegram import keyboards
        keyboard = keyboards.main_menu_keyboard()
        
        await query.edit_message_text(
            "❌ Операция отменена\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    
    async def _handle_back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата в главное меню"""
        query = update.callback_query
        await query.answer()
        
        from infrastructure.telegram import keyboards
        keyboard = keyboards.main_menu_keyboard()
        
        await query.edit_message_text(
            "🏠 Главное меню\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    
    async def _handle_back_to_manage_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата к управлению чатами"""
        query = update.callback_query
        await query.answer()
        
        await self.chat_handlers.manage_chats_handler(update, context)
    
    async def _handle_back_to_chat_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата к настройкам чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            chat_id = context.user_data.get('selected_chat_id')
            if not chat_id:
                await query.edit_message_text(
                    "❌ Чат не выбран"
                )
                return
            
            # Возвращаемся к настройкам чата
            await self.chat_handlers.show_chat_settings(update, context, chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_back_to_chat_settings: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при возврате к настройкам чата"
            )
    
    async def _handle_back_to_chat_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик возврата к управлению чатами"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Возвращаемся к управлению чатами
            await self.chat_handlers.manage_chats_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_back_to_chat_management: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при возврате к управлению чатами"
            )
