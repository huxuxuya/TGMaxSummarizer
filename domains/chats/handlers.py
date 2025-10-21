from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .service import ChatService
from .models import Chat, Message, GroupVKChat
from shared.utils import format_success_message, format_error_message, format_chat_stats
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class ChatHandlers:
    """Обработчики для работы с чатами"""
    
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
    
    async def manage_chats_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик управления чатами"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            
            # Проверяем, есть ли выбранная группа в контексте
            selected_group_id = context.user_data.get('selected_group_id')
            
            if selected_group_id:
                # Если есть выбранная группа, используем клавиатуру для группы
                keyboard = keyboards.group_chat_management_keyboard(selected_group_id)
                group_info = self.chat_service.get_group(selected_group_id)
                group_name = group_info.group_name if group_info else f"Группа {selected_group_id}"
                
                await query.edit_message_text(
                    f"📊 [Управление чатами] VK MAX\n\n"
                    f"[Группа]: {group_name}\n\n"
                    f"Выберите действие:",
                    reply_markup=keyboard
                )
            else:
                # Если нет выбранной группы, используем общую клавиатуру
                keyboard = keyboards.chat_management_keyboard()
                
                await query.edit_message_text(
                    "📊 [Управление чатами] VK MAX\n\n"
                    "Выберите действие:",
                    reply_markup=keyboard
                )
            
        except Exception as e:
            logger.error(f"Ошибка в manage_chats_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def add_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик добавления чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_add_method_keyboard()
            
            await query.edit_message_text(
                "➕ [Добавление чата] VK MAX\n\n"
                "Выберите способ добавления:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в add_chat_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def list_chats_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик списка чатов"""
        query = update.callback_query
        await query.answer()
        
        try:
            group_id = context.user_data.get('selected_group_id')
            if not group_id:
                await query.edit_message_text(
                    "❌ Группа не выбрана"
                )
                return
            
            chats = self.chat_service.get_group_vk_chats(group_id)
            
            if not chats:
                await query.edit_message_text(
                    "📋 [Список чатов] пуст\n\n"
                    "Добавьте чаты VK MAX для анализа."
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_list_keyboard(chats, context="quick")  # ИЗМЕНЕНО
            
            chat_list_text = "📋 [Список чатов] VK MAX:\n\n"
            for chat in chats:
                chat_list_text += f"💬 {chat.chat_name}\n"
            
            await query.edit_message_text(
                chat_list_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в list_chats_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def chat_settings_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('chat_settings_', '', 1)
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_settings_keyboard(vk_chat_id)
            
            chat_info = self.chat_service.get_chat(vk_chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {vk_chat_id}"
            
            await query.edit_message_text(
                f"⚙️ [Настройки чата]: {chat_name}\n\n"
                "Выберите действие:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в chat_settings_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def chat_stats_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик статистики чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('chat_stats_', '', 1)
            
            stats = self.chat_service.get_chat_stats(vk_chat_id)
            stats_text = format_chat_stats(stats)
            
            from infrastructure.telegram import keyboards
            # Создаем клавиатуру с кнопкой "Назад" к меню чата
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=f"quick_chat_{vk_chat_id}")]]
            
            await query.edit_message_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в chat_stats_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def load_messages_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик загрузки сообщений"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('load_messages_', '', 1)
            
            # Проверяем, есть ли уже сообщения в чате
            last_timestamp = self.chat_service.get_last_message_timestamp(vk_chat_id)
            
            if last_timestamp:
                # Если сообщения уже есть, предлагаем выбор
                from infrastructure.telegram import keyboards
                keyboard = [
                    [InlineKeyboardButton("🔄 Загрузить только новые", callback_data=f"load_new_messages_{vk_chat_id}")],
                    [InlineKeyboardButton("🔄 Загрузить все заново", callback_data=f"load_all_messages_{vk_chat_id}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{vk_chat_id}")]
                ]
                
                await query.edit_message_text(
                    "📊 В чате уже есть сообщения\n\n"
                    "Выберите тип загрузки:",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # Если сообщений нет, загружаем все
                await self._load_messages_worker(update, context, vk_chat_id, load_only_new=False)
            
        except Exception as e:
            logger.error(f"Ошибка в load_messages_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def _load_messages_worker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, vk_chat_id: str, load_only_new: bool = False):
        """Рабочий метод загрузки сообщений"""
        query = update.callback_query
        
        try:
            await query.edit_message_text(
                f"🔄 {'Загружаем новые сообщения' if load_only_new else 'Загружаем сообщения'}...\n\n"
                "Это может занять некоторое время."
            )
            
            from infrastructure.vk.client import VKMaxClient
            from core.config import load_config
            
            config = load_config()
            vk_client = VKMaxClient(config['bot'].vk_max_token)
            
            if not await vk_client.connect():
                from infrastructure.telegram import keyboards
                keyboard = keyboards.chat_quick_menu_keyboard(vk_chat_id)
                await query.edit_message_text(
                    "❌ Не удалось подключиться к VK MAX",
                    reply_markup=keyboard
                )
                return
            
            # Загружаем сообщения
            if load_only_new:
                # Получаем timestamp последнего сообщения для остановки загрузки
                last_timestamp = self.chat_service.get_last_message_timestamp(vk_chat_id)
                messages = await vk_client.load_chat_messages(vk_chat_id, days_back=7, load_only_new=True, last_timestamp=last_timestamp)
            else:
                messages = await vk_client.load_chat_messages(vk_chat_id, days_back=7, load_only_new=False)
            
            if not messages:
                message_type = "новых" if load_only_new else ""
                from infrastructure.telegram import keyboards
                keyboard = keyboards.chat_quick_menu_keyboard(vk_chat_id)
                await query.edit_message_text(
                    f"❌ {'Нет новых сообщений' if load_only_new else 'Не удалось загрузить сообщения'}",
                    reply_markup=keyboard
                )
                return
            
            # Сохраняем в БД
            formatted_messages = await vk_client.format_messages_for_db(messages, vk_chat_id)
            saved_count = self.chat_service.save_messages(formatted_messages)
            
            message_type = "новых" if load_only_new else ""
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_quick_menu_keyboard(vk_chat_id)
            await query.edit_message_text(
                format_success_message(
                    f"Загружено {saved_count} {message_type} сообщений"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _load_messages_worker: {e}")
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_quick_menu_keyboard(vk_chat_id)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def remove_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик удаления чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            group_id = context.user_data.get('selected_group_id')
            if not group_id:
                await query.edit_message_text(
                    "❌ Группа не выбрана"
                )
                return
            
            chats = self.chat_service.get_group_vk_chats(group_id)
            
            if not chats:
                await query.edit_message_text(
                    "❌ Нет чатов для удаления"
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_list_keyboard(chats)
            
            await query.edit_message_text(
                "❌ [Удаление чата]\n\n"
                "Выберите чат для удаления:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в remove_chat_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Извлекаем chat_id из callback_data
            chat_id = query.data.split('_')[2]
            user_id = update.effective_user.id
            group_id = context.user_data.get('selected_group_id')
            
            context.user_data['selected_chat_id'] = chat_id
            context.user_data['last_chat_id'] = chat_id
            
            # Сохраняем последний открытый чат для пользователя в группе
            if group_id:
                from domains.users.service import UserService
                from core.database.connection import DatabaseConnection
                from core.config import load_config
                
                config = load_config()
                db_connection = DatabaseConnection(config['database'].path)
                user_service = UserService(db_connection)
                user_service.set_last_chat(user_id, group_id, chat_id)
            
            # Получаем информацию о чате
            chat_info = self.chat_service.get_chat(chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {chat_id}"
            
            # Получаем статистику чата
            stats = self.chat_service.get_chat_stats(chat_id)
            
            # Формируем текст с информацией о чате
            text = f"📊 [Статистика чата]\n\n"
            text += f"💬 Чат: {chat_name}\n\n"
            text += f"📊 *Статистика:*\n"
            text += f"• Всего сообщений: {stats.total_messages}\n"
            text += f"• Дней загружено: {stats.days_count}\n\n"
            
            if stats.recent_days:
                text += "📅 *Последние дни:*\n"
                for day in stats.recent_days[:5]:
                    text += f"• {day['date']} ({day['count']} сообщений)\n"
            
            # Создаем клавиатуру настроек чата
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_settings_keyboard(chat_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_chat_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def show_chat_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Показать настройки чата (для использования из других обработчиков)"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем информацию о чате
            chat_info = self.chat_service.get_chat(chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {chat_id}"
            
            # Получаем статистику чата
            stats = self.chat_service.get_chat_stats(chat_id)
            
            # Формируем текст с информацией о чате
            from infrastructure.telegram.formatter import TelegramFormatter
            text = f"📊 [Статистика чата]\n\n"
            text += f"💬 Чат: {TelegramFormatter.escape_markdown_v1(chat_name)}\n\n"
            text += f"📊 *Статистика:*\n"
            text += f"• Всего сообщений: {stats.total_messages}\n"
            text += f"• Дней загружено: {stats.days_count}\n\n"
            
            if stats.recent_days:
                text += "📅 *Последние дни:*\n"
                for day in stats.recent_days[:5]:
                    text += f"• {day['date']} ({day['count']} сообщений)\n"
            
            # Создаем клавиатуру настроек чата
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_settings_keyboard(chat_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в show_chat_settings: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def quick_chat_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое меню чата"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('quick_chat_', '', 1)
            user_id = update.effective_user.id
            group_id = context.user_data.get('selected_group_id')
            
            context.user_data['selected_chat_id'] = vk_chat_id
            context.user_data['last_chat_id'] = vk_chat_id  # Сохраняем для быстрых действий
            
            # Сохраняем последний открытый чат для пользователя в группе
            if group_id:
                from domains.users.service import UserService
                from core.database.connection import DatabaseConnection
                from core.config import load_config
                
                config = load_config()
                db_connection = DatabaseConnection(config['database'].path)
                user_service = UserService(db_connection)
                user_service.set_last_chat(user_id, group_id, vk_chat_id)
            
            chat_info = self.chat_service.get_chat(vk_chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {vk_chat_id}"
            
            stats = self.chat_service.get_chat_stats(vk_chat_id)
            
            from infrastructure.telegram.formatter import TelegramFormatter
            text = f"📊 [Статистика чата]\n\n"
            text += f"💬 Чат: {TelegramFormatter.escape_markdown_v1(chat_name)}\n\n"
            text += f"📊 *Статистика:*\n"
            text += f"• Всего сообщений: {stats.total_messages}\n"
            text += f"• Дней загружено: {stats.days_count}\n\n"
            
            if stats.recent_days:
                text += "📅 *Последние дни:*\n"
                for day in stats.recent_days[:3]:
                    text += f"• {day['date']} ({day['count']} сообщений)\n"
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_quick_menu_keyboard(vk_chat_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в quick_chat_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def quick_create_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое создание суммаризации"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('quick_create_', '', 1)
            context.user_data['selected_chat_id'] = vk_chat_id
            
            # Получаем доступные даты для анализа
            from domains.summaries.service import SummaryService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            summary_service = SummaryService(db_connection)
            
            # Получаем даты с сообщениями
            stats = self.chat_service.get_chat_stats(vk_chat_id)
            
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
            keyboard = keyboards.create_summary_keyboard(vk_chat_id, available_dates)
            
            chat_info = self.chat_service.get_chat(vk_chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {vk_chat_id}"
            
            # Получаем текущую модель и провайдер
            current_provider = context.user_data.get('confirmed_provider', 'Не выбрано')
            current_model = context.user_data.get('selected_model_id', 'Не выбрано')
            
            await query.edit_message_text(
                f"📝 [Создание суммаризации]\n\n"
                f"💬 Чат: {chat_name}\n"
                f"🤖 Провайдер: {current_provider}\n"
                f"🧠 Модель: {current_model}\n"
                f"📊 Доступно дат: {len(available_dates)}\n\n"
                f"Выберите дату для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в quick_create_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def all_dates_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все доступные даты"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('all_dates_', '', 1)
            stats = self.chat_service.get_chat_stats(vk_chat_id)
            
            if not stats.recent_days:
                await query.edit_message_text("❌ Нет доступных дат")
                return
            
            # Показываем все даты (не только 3)
            available_dates = [{'date': day['date'], 'count': day['count']} for day in stats.recent_days]
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.create_summary_keyboard(vk_chat_id, available_dates, show_all=True)
            
            await query.edit_message_text(
                f"📅 [Все доступные даты] ({len(available_dates)}):\n\n"
                "Выберите дату для создания суммаризации:",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Ошибка в all_dates_handler: {e}")
            await query.edit_message_text(format_error_message(e))
    
    async def set_schedule_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик установки расписания"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем group_id из контекста или из чата
            group_id = context.user_data.get('selected_group_id')
            if not group_id:
                # Если нет в контексте, берем из чата (для работы в группах)
                if update.effective_chat.type in ['group', 'supergroup']:
                    group_id = update.effective_chat.id
                else:
                    await query.edit_message_text(
                        "❌ Группа не выбрана"
                    )
                    return
            
            # Проверяем права администратора только для групп
            user_id = update.effective_user.id
            
            # Если это группа - проверяем права администратора
            if update.effective_chat.type in ['group', 'supergroup']:
                administrators = await context.bot.get_chat_administrators(group_id)
                admin_ids = [admin.user.id for admin in administrators]
                
                if user_id not in admin_ids:
                    await query.edit_message_text(
                        "❌ Только администраторы могут устанавливать расписание"
                    )
                    return
            
            # Устанавливаем флаги для загрузки расписания
            context.user_data['uploading_schedule'] = True
            context.user_data['schedule_group_id'] = group_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.schedule_management_keyboard(False, False)  # Нет фото, нет анализа
            
            await query.edit_message_text(
                "📅 [Установка расписания]\n\n"
                "Отправьте фото расписания в следующем сообщении.\n\n"
                "Или отправьте /cancel для отмены.",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в set_schedule_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def delete_schedule_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик удаления расписания"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем group_id из контекста или из чата
            group_id = context.user_data.get('selected_group_id')
            if not group_id:
                # Если нет в контексте, берем из чата (для работы в группах)
                if update.effective_chat.type in ['group', 'supergroup']:
                    group_id = update.effective_chat.id
                else:
                    await query.edit_message_text(
                        "❌ Группа не выбрана"
                    )
                    return
            
            # Проверяем права администратора только для групп
            user_id = update.effective_user.id
            
            # Если это группа - проверяем права администратора
            if update.effective_chat.type in ['group', 'supergroup']:
                administrators = await context.bot.get_chat_administrators(group_id)
                admin_ids = [admin.user.id for admin in administrators]
                
                if user_id not in admin_ids:
                    await query.edit_message_text(
                        "❌ Только администраторы могут удалять расписание"
                    )
                    return
            
            # Удаляем расписание
            success = self.chat_service.delete_schedule_photo(group_id)
            
            # Удаляем результаты анализа расписания
            if success:
                from core.database.connection import DatabaseConnection
                from core.config import load_config
                from .repository import ScheduleAnalysisRepository
                
                config = load_config()
                db_connection = DatabaseConnection(config['database'].path)
                schedule_analysis_repo = ScheduleAnalysisRepository(db_connection)
                schedule_analysis_repo.delete_schedule_analysis(group_id)
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.schedule_management_keyboard(False, False)  # После удаления нет фото и анализа
            
            if success:
                await query.edit_message_text(
                    "✅ Расписание удалено",
                    reply_markup=keyboard
                )
            else:
                await query.edit_message_text(
                    "❌ Не удалось удалить расписание",
                    reply_markup=keyboard
                )
            
        except Exception as e:
            logger.error(f"Ошибка в delete_schedule_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def show_schedule_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик показа расписания"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем group_id из контекста или из чата
            group_id = context.user_data.get('selected_group_id')
            if not group_id:
                # Если нет в контексте, берем из чата (для работы в группах)
                if update.effective_chat.type in ['group', 'supergroup']:
                    group_id = update.effective_chat.id
                else:
                    await query.edit_message_text(
                        "❌ Группа не выбрана"
                    )
                    return
            
            # Получаем file_id расписания
            file_id = self.chat_service.get_schedule_photo(group_id)
            
            if file_id:
                # Отправляем фото расписания в личные сообщения
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=file_id,
                    caption="📅 Расписание группы"
                )
            else:
                await query.edit_message_text(
                    "❌ Расписание не установлено\n\n"
                    "Используйте кнопку 'Установить расписание' для загрузки фото."
                )
            
        except Exception as e:
            logger.error(f"Ошибка в show_schedule_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def schedule_command_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /schedule"""
        try:
            chat_id = update.effective_chat.id
            
            # Получаем file_id расписания
            file_id = self.chat_service.get_schedule_photo(chat_id)
            
            if file_id:
                # Отправляем фото расписания
                await update.message.reply_photo(
                    photo=file_id,
                    caption="📅 Расписание группы"
                )
            else:
                await update.message.reply_text(
                    "❌ Расписание не установлено\n\n"
                    "Используйте кнопку 'Установить расписание' для загрузки фото."
                )
            
        except Exception as e:
            logger.error(f"Ошибка в schedule_command_handler: {e}")
            await update.message.reply_text(
                "❌ Ошибка при получении расписания"
            )