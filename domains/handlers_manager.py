from telegram import Update
from telegram.ext import ContextTypes
from .users.handlers import UserHandlers
from .chats.handlers import ChatHandlers
from .ai.handlers import AIHandlers
from .summaries.handlers import SummaryHandlers
from .command_registry import CommandRegistry
from core.app_context import get_app_context
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class HandlersManager:
    """Менеджер всех обработчиков бота"""
    
    def __init__(self):
        # Use singleton services from app context
        ctx = get_app_context()
        
        self.user_handlers = UserHandlers(ctx.user_service)
        self.chat_handlers = ChatHandlers(ctx.chat_service)
        self.ai_handlers = AIHandlers(ctx.ai_service, ctx.user_service)
        self.summary_handlers = SummaryHandlers(ctx.summary_service, ctx.user_service)
        
        # Setup command registry
        self.registry = CommandRegistry()
        self._register_commands()
    
    def _register_commands(self):
        """Register all callback handlers"""
        # Exact matches
        self.registry.register(CallbackActions.MANAGE_CHATS, 
                             self.chat_handlers.manage_chats_handler)
        self.registry.register(CallbackActions.ADD_CHAT, 
                             self.chat_handlers.add_chat_handler)
        self.registry.register(CallbackActions.LIST_CHATS, 
                             self.chat_handlers.list_chats_handler)
        self.registry.register(CallbackActions.REMOVE_CHAT, 
                             self.chat_handlers.remove_chat_handler)
        self.registry.register(CallbackActions.SELECT_AI_PROVIDER, 
                             self.ai_handlers.select_ai_provider_handler)
        self.registry.register(CallbackActions.CHANGE_GROUP, 
                             self.user_handlers.change_group_handler)
        self.registry.register(CallbackActions.CANCEL, 
                             self._handle_cancel)
        self.registry.register("back", 
                             self._handle_generic_back)
        self.registry.register(CallbackActions.BACK_TO_MAIN, 
                             self._handle_back_to_main)
        self.registry.register(CallbackActions.BACK_TO_MANAGE_CHATS, 
                             self._handle_back_to_manage_chats)
        self.registry.register(CallbackActions.BACK_TO_CHAT_SETTINGS, 
                             self._handle_back_to_chat_settings)
        
        # Pattern matches
        self.registry.register("select_group_*", 
                             self.user_handlers.select_group_handler)
        self.registry.register("select_provider:*", 
                             self.ai_handlers.select_provider_handler)
        self.registry.register("confirm_provider:*", 
                             self.ai_handlers.confirm_provider_handler)
        self.registry.register("chat_settings_*", 
                             self.chat_handlers.chat_settings_handler)
        self.registry.register("chat_stats_*", 
                             self.chat_handlers.chat_stats_handler)
        self.registry.register("load_messages_*", 
                             self.chat_handlers.load_messages_handler)
        # These will be registered after the helper methods are created
        self.registry.register("select_chat_*", 
                             self.chat_handlers.select_chat_handler)
        self.registry.register("check_summary_*", 
                             self.summary_handlers.check_summary_handler)
        self.registry.register("publish_summary_*", 
                             self.summary_handlers.publish_summary_handler)
        self.registry.register("publish_summary_html_*", 
                             self.summary_handlers.publish_summary_html_handler)
        self.registry.register("select_date_*", 
                             self.summary_handlers.select_date_handler)
        
        # Special handlers
        self.registry.register("select_model_for_analysis", 
                             self.ai_handlers.select_model_for_analysis_handler)
        self.registry.register("back_to_chat_management", 
                             self._handle_back_to_chat_management)
        self.registry.register("ai_provider_settings", 
                             self.ai_handlers.ai_provider_settings_handler)
        self.registry.register("ai_provider_defaults", 
                             self.ai_handlers.ai_provider_defaults_handler)
        self.registry.register("quick_create_*", 
                             self.chat_handlers.quick_create_handler)
        self.registry.register("quick_chat_*", 
                             self.chat_handlers.quick_chat_handler)
        self.registry.register("quick_actions", 
                             self._handle_quick_actions)
        self.registry.register("settings_menu", 
                             self._handle_settings_menu)
        
        # AI Provider handlers
        self.registry.register("ai_provider_status", 
                             self.ai_handlers.ai_provider_status_handler)
        self.registry.register("check_providers_availability", 
                             self.ai_handlers.check_providers_availability_handler)
        self.registry.register("openrouter_model_selection", 
                             self.ai_handlers.openrouter_model_selection_handler)
        self.registry.register("select_openrouter_model:*", 
                             self.ai_handlers.select_openrouter_model_handler)
        self.registry.register("confirm_openrouter_model:*", 
                             self.ai_handlers.confirm_openrouter_model_handler)
        self.registry.register("top5_models_selection", 
                             self.ai_handlers.top5_models_selection_handler)
        self.registry.register("select_top5_model:*", 
                             self.ai_handlers.select_top5_model_handler)
        self.registry.register("confirm_top5_model:*", 
                             self.ai_handlers.confirm_top5_model_handler)
        self.registry.register("ollama_model_selection", 
                             self.ai_handlers.ollama_model_selection_handler)
        self.registry.register("select_ollama_model:*", 
                             self.ai_handlers.select_ollama_model_handler)
        
        # Summary handlers
        self.registry.register("publish_menu_*", 
                             self.summary_handlers.publish_menu_handler)
        self.registry.register("select_publish_date_*", 
                             self.summary_handlers.select_publish_date_handler)
        self.registry.register("select_scenario_*", 
                             self.summary_handlers.select_scenario_handler)
        self.registry.register("scenario_*", 
                             self.summary_handlers.select_scenario_handler)
        self.registry.register("run_summary_*", 
                             self.summary_handlers.run_summary_handler)
        self.registry.register("create_for_date_*", 
                             self.summary_handlers.create_for_date_handler)
        self.registry.register("all_dates_*", 
                             self.chat_handlers.all_dates_handler)
        
        # User handlers
        self.registry.register("schedule_settings", 
                             self.user_handlers.schedule_settings_handler)
        
        # Chat handlers
        self.registry.register("select_chat_quick", 
                             self._handle_select_chat_quick)
        self.registry.register("select_chat_for_action", 
                             self._handle_select_chat_for_action)
        
        # Pattern handlers for complex callbacks
        self.registry.register("change_model_for_summary_*", 
                             self._handle_change_model_for_summary)
        self.registry.register("publish_md_*", 
                             self._handle_publish_md)
        self.registry.register("publish_html_*", 
                             self._handle_publish_html)
        self.registry.register("scenario_defaults", 
                             self.ai_handlers.scenario_defaults_handler)
        self.registry.register("set_default_scenario:*", 
                             self.ai_handlers.set_default_scenario_handler)
        self.registry.register("clear_ai_settings", 
                             self.ai_handlers.clear_ai_settings_handler)
        
        # Add helper methods for pattern handlers
        self._handle_load_new_messages = self._create_load_messages_handler(True)
        self._handle_load_all_messages = self._create_load_messages_handler(False)
        
        # Register the dynamic handlers
        self.registry.register("load_new_messages_*", 
                             self._handle_load_new_messages)
        self.registry.register("load_all_messages_*", 
                             self._handle_load_all_messages)
    
    def _create_load_messages_handler(self, load_only_new: bool):
        """Create a handler for load messages pattern"""
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            data = query.data
            chat_id = data.split("_")[3]
            await self.chat_handlers._load_messages_worker(update, context, chat_id, load_only_new=load_only_new)
        return handler
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главный обработчик /start"""
        await self.user_handlers.start_handler(update, context)
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        data = query.data
        
        try:
            success = await self.registry.dispatch(query.data, update, context)
            if not success:
                await query.edit_message_text("❌ Неизвестная команда")
                
        except Exception as e:
            logger.error(f"Ошибка в callback_query_handler: {e}", exc_info=True)
            await query.edit_message_text("❌ Произошла ошибка")
    
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
        
        try:
            user_id = update.effective_user.id
            
            # ALWAYS initialize chat_service
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            # Try cache for user_groups
            from shared.cache import cache
            cache_key = f"user_groups_{user_id}"
            user_groups = cache.get(cache_key)
            
            if user_groups is None:
                user_groups = chat_service.get_user_groups(user_id)
                cache.set(cache_key, user_groups, 120)
            
            if len(user_groups) == 1:
                # Если группа одна - показываем главное меню с чатами
                group_id = user_groups[0].group_id
                context.user_data['selected_group_id'] = group_id
                
                group_chats = chat_service.get_group_vk_chats(group_id)
                
                from infrastructure.telegram import keyboards
                keyboard = keyboards.main_menu_keyboard(chats_count=len(group_chats), chats=group_chats)
                
                await query.edit_message_text(
                    f"🏠 Главное меню\n\n"
                    f"✅ Группа: {user_groups[0].group_name}\n\n"
                    f"Выберите действие:",
                    reply_markup=keyboard
                )
            else:
                # Если групп несколько - показываем выбор групп
                from infrastructure.telegram import keyboards
                keyboard = keyboards.group_selection_keyboard(user_groups)
                
                await query.edit_message_text(
                    "🏠 Главное меню\n\n"
                    "Выберите группу для работы:",
                    reply_markup=keyboard
                )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_back_to_main: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при возврате в главное меню"
            )
    
    async def _handle_generic_back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик универсальной кнопки 'Назад'"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Пытаемся вернуться в главное меню
            await self._handle_back_to_main(update, context)
        except Exception as e:
            logger.error(f"Ошибка в _handle_generic_back: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при возврате назад"
            )
    
    async def _handle_all_dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик показа всех дат для создания суммаризации"""
        query = update.callback_query
        await query.answer()
        
        try:
            # all_dates_{vk_chat_id}
            vk_chat_id = query.data.replace('all_dates_', '', 1)
            context.user_data['selected_chat_id'] = vk_chat_id
            
            # Получаем все даты с сообщениями
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            stats = chat_service.get_chat_stats(vk_chat_id)
            
            if not stats.recent_days:
                await query.edit_message_text(
                    "❌ Нет сообщений для анализа\n\n"
                    "Сначала загрузите сообщения из VK MAX."
                )
                return
            
            # Преобразуем в формат для клавиатуры
            available_dates = []
            for day in stats.recent_days:
                available_dates.append({
                    'date': day['date'],
                    'count': day['count']
                })
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.create_summary_keyboard(vk_chat_id, available_dates, show_all=True)
            
            chat_info = chat_service.get_chat(vk_chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {vk_chat_id}"
            
            # Получаем текущую модель и провайдер
            current_provider = context.user_data.get('confirmed_provider', 'Не выбрано')
            current_model = context.user_data.get('selected_model_id', 'Не выбрано')
            
            await query.edit_message_text(
                f"📝 Создание суммаризации\n\n"
                f"💬 Чат: {chat_name}\n"
                f"🤖 Провайдер: {current_provider}\n"
                f"🧠 Модель: {current_model}\n"
                f"📊 Всего дат: {len(available_dates)}\n\n"
                f"Выберите дату для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_all_dates: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при загрузке дат"
            )
    
    async def _handle_schedule_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек расписания"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Пока что показываем заглушку
            from infrastructure.telegram import keyboards
            keyboard = keyboards.schedule_keyboard()
            
            await query.edit_message_text(
                "📅 Настройки расписания\n\n"
                "Функция в разработке...",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_schedule_settings: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при открытии настроек расписания"
            )
    
    async def _handle_change_model_for_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик смены модели для суммаризации"""
        query = update.callback_query
        await query.answer()
        
        try:
            # change_model_for_summary_{vk_chat_id}_{date}_{scenario}
            parts = query.data.replace('change_model_for_summary_', '', 1).split('_')
            scenario = parts[-1]
            date = parts[-2]
            vk_chat_id = '_'.join(parts[:-2])
            
            # Сохраняем параметры
            context.user_data['selected_scenario'] = scenario
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            
            # Показываем выбор модели
            await self.ai_handlers.select_ai_provider_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_change_model_for_summary: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при смене модели"
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
    
    async def _handle_quick_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик быстрых действий"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем последний выбранный чат
            last_chat_id = context.user_data.get('last_chat_id')
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.quick_actions_keyboard(last_chat_id)
            
            text = "⚡ Быстрые действия\n\n"
            if last_chat_id:
                text += f"💬 Последний чат: {last_chat_id}\n"
                text += "Выберите действие для этого чата:"
            else:
                text += "Выберите чат для выполнения действий:"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_quick_actions: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при открытии быстрых действий"
            )
    
    async def _handle_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик меню настроек"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.settings_menu_keyboard()
            
            await query.edit_message_text(
                "⚙️ Настройки\n\n"
                "Выберите категорию настроек:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_settings_menu: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при открытии настроек"
            )
    
    async def _handle_publish_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик меню публикации"""
        # ВЫЗЫВАЕМ ПРАВИЛЬНЫЙ обработчик
        await self.summary_handlers.publish_menu_handler(update, context)
    
    async def _handle_chat_advanced(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик расширенных настроек чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('chat_advanced_', '', 1)
            
            # Показываем старое меню настроек чата
            await self.chat_handlers.show_chat_settings(update, context, vk_chat_id)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_chat_advanced: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при открытии настроек чата"
            )
    
    async def _handle_select_chat_quick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик быстрого выбора чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Показываем список чатов
            await self.chat_handlers.list_chats_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_select_chat_quick: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при выборе чата"
            )
    
    async def _handle_select_chat_for_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора чата для действия"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Показываем список чатов
            await self.chat_handlers.list_chats_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_select_chat_for_action: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при выборе чата"
            )
    
    async def _handle_publish_md(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации в Markdown формате"""
        query = update.callback_query
        await query.answer()
        
        try:
            # publish_md_{vk_chat_id}_{date}
            parts = query.data.split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[2:-1])
            
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            context.user_data['use_html_format'] = False  # Markdown format
            
            # Вызываем существующий обработчик публикации
            await self.summary_handlers.publish_to_group_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_publish_md: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при публикации"
            )
    
    async def _handle_publish_html(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации в HTML формате"""
        query = update.callback_query
        await query.answer()
        
        try:
            # publish_html_{vk_chat_id}_{date}
            parts = query.data.split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[2:-1])
            
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            context.user_data['use_html_format'] = True  # HTML format
            
            # Вызываем существующий обработчик публикации
            await self.summary_handlers.publish_to_group_handler(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_publish_html: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при публикации"
            )
