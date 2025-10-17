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
            keyboard = keyboards.chat_management_keyboard()
            
            await query.edit_message_text(
                "📊 Управление чатами VK MAX\n\n"
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
                "➕ Добавление чата VK MAX\n\n"
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
                    "📋 Список чатов пуст\n\n"
                    "Добавьте чаты VK MAX для анализа."
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_list_keyboard(chats)
            
            chat_list_text = "📋 Список чатов VK MAX:\n\n"
            for chat in chats:
                chat_list_text += f"💬 {chat['chat_name']}\n"
            
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
            vk_chat_id = query.data.split('_')[-1]
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.chat_settings_keyboard(vk_chat_id)
            
            chat_info = self.chat_service.get_chat(vk_chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {vk_chat_id}"
            
            await query.edit_message_text(
                f"⚙️ Настройки чата: {chat_name}\n\n"
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
            vk_chat_id = query.data.split('_')[-1]
            
            stats = self.chat_service.get_chat_stats(vk_chat_id)
            stats_text = format_chat_stats(stats)
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            await query.edit_message_text(
                stats_text,
                reply_markup=keyboard,
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
            vk_chat_id = query.data.split('_')[-1]
            
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
                await query.edit_message_text(
                    "❌ Не удалось подключиться к VK MAX"
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
                await query.edit_message_text(
                    f"❌ {'Нет новых сообщений' if load_only_new else 'Не удалось загрузить сообщения'}"
                )
                return
            
            # Сохраняем в БД
            formatted_messages = await vk_client.format_messages_for_db(messages, vk_chat_id)
            saved_count = self.chat_service.save_messages(formatted_messages)
            
            message_type = "новых" if load_only_new else ""
            await query.edit_message_text(
                format_success_message(
                    f"Загружено {saved_count} {message_type} сообщений"
                )
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _load_messages_worker: {e}")
            await query.edit_message_text(
                format_error_message(e)
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
                "❌ Удаление чата\n\n"
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
            context.user_data['selected_chat_id'] = chat_id
            
            # Получаем информацию о чате
            chat_info = self.chat_service.get_chat(chat_id)
            chat_name = chat_info.chat_name if chat_info else f"Чат {chat_id}"
            
            # Получаем статистику чата
            stats = self.chat_service.get_chat_stats(chat_id)
            
            # Формируем текст с информацией о чате
            text = f"💬 Чат: {chat_name}\n\n"
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
            text = f"💬 Чат: {chat_name}\n\n"
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