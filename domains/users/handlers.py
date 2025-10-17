from telegram import Update
from telegram.ext import ContextTypes
from .service import UserService
from .models import User
from shared.utils import format_success_message, format_error_message
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class UserHandlers:
    """Обработчики для работы с пользователями"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        try:
            user_model = User(
                user_id=user.id,
                username=user.username,
                is_admin=False
            )
            
            self.user_service.create_or_update_user(
                user_model.user_id, 
                user_model.username, 
                user_model.is_admin
            )
            
            # Load user preferences into context
            self.user_service.load_user_preferences_to_context(user.id, context)
            
            if chat.type == "private":
                await self._handle_private_start(update, context)
            else:
                await self._handle_group_start(update, context)
                
        except Exception as e:
            logger.error(f"Ошибка в start_handler: {e}")
            await update.effective_message.reply_text(
                format_error_message(e)
            )
    
    async def _handle_private_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start в личных сообщениях"""
        user = update.effective_user
        
        user_groups = self.user_service.get_user_groups(user.id)
        
        if not user_groups:
            await update.effective_message.reply_text(
                "👋 Добро пожаловать!\n\n"
                "Для работы с ботом добавьте его в группу и сделайте администратором."
            )
            return
        
        if len(user_groups) == 1:
            group_id = user_groups[0].group_id
            context.user_data['selected_group_id'] = group_id
            
            # Получаем список чатов для нового главного меню
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            # Получаем чаты единственной группы
            group_id = user_groups[0].group_id
            chats = chat_service.get_group_vk_chats(group_id)
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.main_menu_keyboard(chats_count=len(chats), chats=chats)
            
            await update.effective_message.reply_text(
                f"👋 Добро пожаловать!\n\n"
                f"✅ Выбрана группа: {user_groups[0].group_name}\n\n"
                f"📊 [Главное меню] Управление чатами VK MAX",
                reply_markup=keyboard
            )
        else:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.group_selection_keyboard(user_groups)
            
            await update.effective_message.reply_text(
                "👋 Добро пожаловать!\n\n"
                "[Выберите группу] для работы:",
                reply_markup=keyboard
            )
    
    async def _handle_group_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start в группе"""
        chat = update.effective_chat
        user = update.effective_user
        
        from domains.chats.models import Group, GroupUser
        from domains.chats.service import ChatService
        from core.database.connection import DatabaseConnection
        from core.config import load_config
        
        config = load_config()
        db_connection = DatabaseConnection(config['database'].path)
        chat_service = ChatService(db_connection)
        
        group = Group(
            group_id=chat.id,
            group_name=chat.title
        )
        chat_service.add_group(group)
        
        group_user = GroupUser(
            group_id=chat.id,
            user_id=user.id,
            is_admin=True
        )
        chat_service.add_group_user(group_user)
        
        await update.effective_message.reply_text(
            f"✅ Бот добавлен в группу '{chat.title}'\n\n"
            f"Используйте /start в личных сообщениях для управления чатами и расписанием."
        )
    
    async def change_group_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик смены группы"""
        user = update.effective_user
        
        try:
            user_groups = self.user_service.get_user_groups(user.id)
            
            if not user_groups:
                await update.effective_message.reply_text(
                    "❌ У вас нет доступных групп.\n\n"
                    "Добавьте бота в группу и сделайте администратором."
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.group_selection_keyboard(user_groups)
            
            await update.effective_message.reply_text(
                "[Выберите группу] для работы:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в change_group_handler: {e}")
            await update.effective_message.reply_text(
                format_error_message(e)
            )
    
    async def select_group_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора группы"""
        query = update.callback_query
        await query.answer()
        
        try:
            group_id = int(query.data.split('_')[-1])
            user_id = update.effective_user.id
            context.user_data['selected_group_id'] = group_id
            
            # Получаем чаты выбранной группы
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            group_chats = chat_service.get_group_vk_chats(group_id)
            
            # Получаем название группы
            group_info = chat_service.get_group(group_id)
            group_name = group_info.group_name if group_info else f"Группа {group_id}"
            
            # Проверяем, есть ли последний открытый чат для этой группы
            last_chat_id = self.user_service.get_last_chat(user_id, group_id)
            
            if last_chat_id and group_chats:
                # Проверяем, что последний чат все еще существует в группе
                chat_exists = any(chat.chat_id == last_chat_id for chat in group_chats)
                
                if chat_exists:
                    # Автоматически открываем последний чат
                    context.user_data['selected_chat_id'] = last_chat_id
                    context.user_data['last_chat_id'] = last_chat_id
                    
                    # Получаем информацию о чате
                    chat_info = chat_service.get_chat(last_chat_id)
                    chat_name = chat_info.chat_name if chat_info else f"Чат {last_chat_id}"
                    
                    # Получаем статистику чата
                    stats = chat_service.get_chat_stats(last_chat_id)
                    
                    text = f"📊 [Статистика группы и чата]\n\n"
                    text += f"✅ [Группа]: {group_name}\n"
                    text += f"💬 [Чат]: {chat_name}\n\n"
                    text += f"📊 *Статистика:*\n"
                    text += f"• Всего сообщений: {stats.total_messages}\n"
                    text += f"• Дней загружено: {stats.days_count}\n\n"
                    
                    if stats.recent_days:
                        text += "📅 *Последние дни:*\n"
                        for day in stats.recent_days[:3]:
                            text += f"• {day['date']} ({day['count']} сообщений)\n"
                    
                    from infrastructure.telegram import keyboards
                    keyboard = keyboards.chat_quick_menu_keyboard(last_chat_id, group_id)
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    return
            
            # Если последнего чата нет или он не существует, показываем главное меню
            from infrastructure.telegram import keyboards
            keyboard = keyboards.main_menu_keyboard(chats_count=len(group_chats), chats=group_chats)
            
            await query.edit_message_text(
                f"✅ [Группа выбрана]: {group_name}\n\n"
                f"📊 [Главное меню] Управление чатами VK MAX\n\n"
                f"Выберите действие:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_group_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def schedule_settings_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройки расписания публикаций"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="settings_menu")]]
            
            await query.edit_message_text(
                "📅 [Расписание публикаций]\n\n"
                "⚠️ Функция в разработке\n\n"
                "Здесь будет возможность настроить автоматическую публикацию суммаризаций по расписанию.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Ошибка в schedule_settings_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )

