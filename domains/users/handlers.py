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
            group_id = user_groups[0]['group_id']
            context.user_data['selected_group_id'] = group_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_management_keyboard()
            
            await update.effective_message.reply_text(
                f"👋 Добро пожаловать!\n\n"
                f"✅ Выбрана группа: {user_groups[0]['group_name']}\n\n"
                f"📊 Управление чатами VK MAX",
                reply_markup=keyboard
            )
        else:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.group_selection_keyboard(user_groups)
            
            await update.effective_message.reply_text(
                "👋 Добро пожаловать!\n\n"
                "Выберите группу для работы:",
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
            format_success_message(
                f"Бот добавлен в группу '{chat.title}'\n\n"
                "Используйте /start в личных сообщениях для управления чатами."
            )
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
                "Выберите группу для работы:",
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
            context.user_data['selected_group_id'] = group_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_management_keyboard()
            
            await query.edit_message_text(
                f"✅ Группа выбрана\n\n"
                f"📊 Управление чатами VK MAX",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_group_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )

