"""
Обработчики команд и сообщений для Telegram бота
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram_formatter import TelegramFormatter
from telegram_message_sender import TelegramMessageSender

# Используем новый TelegramMessageSender вместо старой функции

from database import DatabaseManager
from vk_integration import VKMaxIntegration
from chat_analyzer import ChatAnalyzer
from keyboards import *
from utils import shorten_callback_data

logger = logging.getLogger(__name__)

class BotHandlers:
    """Класс обработчиков для Telegram бота"""
    
    def __init__(self, db_manager: DatabaseManager, vk_integration: VKMaxIntegration, chat_analyzer: ChatAnalyzer):
        self.db = db_manager
        self.vk = vk_integration
        self.analyzer = chat_analyzer
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Добавляем пользователя в БД
        self.db.add_user(user.id, user.username)
        
        if chat.type == "private":
            # Личные сообщения - показываем выбор группы
            await self._handle_private_start(update, context)
        else:
            # Группа - добавляем в БД и показываем меню
            await self._handle_group_start(update, context)
    
    async def _handle_private_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start в личных сообщениях"""
        user = update.effective_user
        
        # Получаем группы пользователя
        user_groups = self.db.get_user_groups(user.id)
        
        if not user_groups:
            await update.message.reply_text(
                "👋 Добро пожаловать!\n\n"
                "Для работы с ботом добавьте его в группу и сделайте администратором."
            )
            return
        
        # Если группа только одна, сразу переходим к управлению чатами
        if len(user_groups) == 1:
            group_id = user_groups[0]['group_id']
            context.user_data['selected_group_id'] = group_id
            
            keyboard = chat_management_keyboard()
            await update.message.reply_text(
                f"👋 Добро пожаловать!\n\n"
                f"✅ Выбрана группа: {user_groups[0]['group_name']}\n\n"
                f"📊 Управление чатами VK MAX",
                reply_markup=keyboard
            )
        else:
            # Показываем выбор группы
            keyboard = group_selection_keyboard(user_groups)
            await update.message.reply_text(
                "👋 Добро пожаловать!\n\n"
                "Выберите группу для работы:",
                reply_markup=keyboard
            )
    
    async def _handle_group_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start в группе"""
        chat = update.effective_chat
        user = update.effective_user
        
        # Добавляем группу в БД
        self.db.add_group(chat.id, chat.title)
        
        # Добавляем пользователя в группу как админа
        self.db.add_group_user(chat.id, user.id, is_admin=True)
        
        await update.message.reply_text(
            f"✅ Бот добавлен в группу '{chat.title}'\n\n"
            "Теперь вы можете управлять чатами VK MAX через этого бота."
        )
    
    async def callback_query_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "manage_chats":
            await self._handle_manage_chats(update, context)
        elif data == "statistics":
            await self._handle_statistics(update, context)
        elif data == "settings":
            await self._handle_settings(update, context)
        elif data.startswith("select_group_"):
            group_id = int(data.split("_")[2])
            await self._handle_group_selection(update, context, group_id)
        elif data == "add_chat":
            await self._handle_add_chat(update, context)
        elif data == "select_from_list":
            await self._handle_select_from_list(update, context)
        elif data == "enter_chat_id":
            await self._handle_enter_chat_id(update, context)
        elif data.startswith("select_available_chat_"):
            chat_id = data.split("_")[3]
            await self._handle_select_available_chat(update, context, chat_id)
        elif data.startswith("chats_page_"):
            page = int(data.split("_")[2])
            await self._handle_chats_page(update, context, page)
        elif data == "search_chat_by_id":
            await self._handle_search_chat_by_id(update, context)
        elif data.startswith("select_date_"):
            date = data.split("_")[2]
            await self._handle_date_selection(update, context, date)
        elif data.startswith("generate_new_summary_"):
            chat_id = data.split("_")[3]
            date = data.split("_")[4]
            await self._handle_generate_new_summary(update, context, chat_id, date)
        elif data.startswith("improve_summary_"):
            chat_id = data.split("_")[2]
            date = data.split("_")[3]
            await self._handle_improve_summary(update, context, chat_id, date)
        elif data.startswith("view_existing_summary_"):
            chat_id = data.split("_")[3]
            date = data.split("_")[4]
            await self._handle_view_existing_summary(update, context, chat_id, date)
        elif data == "list_chats":
            await self._handle_list_chats(update, context)
        elif data.startswith("select_chat_"):
            chat_id = data.split("_")[2]
            await self._handle_chat_selection(update, context, chat_id)
        elif data.startswith("chat_stats_"):
            chat_id = data.split("_")[2]
            await self._handle_chat_stats(update, context, chat_id)
        elif data.startswith("load_messages_"):
            chat_id = data.split("_")[2]
            await self._handle_load_messages(update, context, chat_id)
        elif data.startswith("load_new_messages_"):
            chat_id = data.split("_")[3]
            await self._load_messages_worker(update, context, chat_id, load_only_new=True)
        elif data.startswith("load_all_messages_"):
            chat_id = data.split("_")[3]
            await self._load_messages_worker(update, context, chat_id, load_only_new=False)
        elif data.startswith("check_summary_"):
            chat_id = data.split("_")[2]
            await self._handle_check_summary(update, context, chat_id)
        elif data.startswith("publish_summary_"):
            parts = data.split("_")
            if len(parts) == 3:
                # Старый формат без даты
                chat_id = parts[2]
                await self._handle_publish_summary(update, context, chat_id)
            elif len(parts) == 4:
                # Новый формат с датой
                chat_id = parts[2]
                date = parts[3]
                await self._handle_publish_summary_with_date(update, context, chat_id, date)
        elif data == "back_to_main":
            await self._handle_back_to_main(update, context)
        elif data == "change_group":
            await self._handle_change_group(update, context)
        elif data == "back_to_manage_chats":
            await self._handle_back_to_manage_chats(update, context)
        elif data == "back_to_chat_settings":
            chat_id = context.user_data.get('selected_chat_id')
            if chat_id:
                await self._handle_chat_selection(update, context, chat_id)
            else:
                await self._handle_back_to_manage_chats(update, context)
        elif data == "back":
            # Универсальная кнопка "Назад" - возвращаемся к настройкам чата
            chat_id = context.user_data.get('selected_chat_id')
            if chat_id:
                await self._handle_chat_selection(update, context, chat_id)
            else:
                await self._handle_back_to_manage_chats(update, context)
        elif data == "cancel":
            await self._handle_cancel(update, context)
        # AI Provider handlers
        elif data == "select_ai_provider":
            await self.ai_provider_selection_handler(update, context)
        elif data.startswith("select_provider:"):
            await self.select_provider_handler(update, context)
        elif data == "ai_provider_status":
            await self.ai_provider_status_handler(update, context)
        elif data == "check_providers_availability":
            await self.check_providers_availability_handler(update, context)
        elif data == "ai_provider_defaults":
            await self.ai_provider_defaults_handler(update, context)
        elif data.startswith("set_default_provider:"):
            await self.set_default_provider_handler(update, context)
        elif data == "ai_provider_settings":
            await self.ai_provider_defaults_handler(update, context)
        # OpenRouter Model handlers
        elif data == "openrouter_model_selection":
            await self.openrouter_model_selection_handler(update, context)
        elif data == "top5_models_selection":
            await self.top5_models_selection_handler(update, context)
        elif data.startswith("select_top5_model:"):
            model_id = data.split(":", 1)[1]
            await self.top5_model_info_handler(update, context, model_id)
        elif data.startswith("confirm_top5_model:"):
            model_id = data.split(":", 1)[1]
            await self.confirm_top5_model_handler(update, context, model_id)
        elif data.startswith("select_openrouter_model:"):
            await self.select_openrouter_model_handler(update, context)
        elif data.startswith("confirm_openrouter_model:"):
            await self.confirm_openrouter_model_handler(update, context)
        # Model selection for analysis handlers
        elif data == "select_model_for_analysis":
            await self.select_model_for_analysis_handler(update, context)
        elif data.startswith("analyze_with_provider:"):
            await self.analyze_with_provider_handler(update, context)
        elif data.startswith("analyze_with_openrouter_model:"):
            await self.analyze_with_openrouter_model_handler(update, context)
        elif data.startswith("analyze_with_openrouter_model_index:"):
            await self.analyze_with_openrouter_model_index_handler(update, context)
    
    async def _handle_manage_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка управления чатами"""
        group_id = context.user_data.get('selected_group_id')
        if not group_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        # Проверяем, есть ли уже чаты в группе
        chats = self.db.get_group_vk_chats(group_id)
        
        if chats:
            # Если чаты есть, сразу показываем их список
            keyboard = chat_list_keyboard(chats)
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "📋 Список чатов VK MAX:",
                reply_markup=keyboard
            )
        else:
            # Если чатов нет, показываем меню управления
            keyboard = chat_management_keyboard()
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "📊 Управление чатами VK MAX\n\n"
                "Чаты не добавлены. Добавьте первый чат:",
                reply_markup=keyboard
            )
    
    async def _handle_statistics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка статистики"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "📈 Статистика\n\n"
            "Функция в разработке...",
            reply_markup=back_keyboard()
        )
    
    async def _handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка настроек"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "🔧 Настройки\n\n"
            "Функция в разработке...",
            reply_markup=back_keyboard()
        )
    
    async def _handle_group_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int):
        """Обработка выбора группы"""
        # Сохраняем выбранную группу в контексте
        context.user_data['selected_group_id'] = group_id
        
        # Получаем название группы для отображения
        user_groups = self.db.get_user_groups(update.effective_user.id)
        group_name = "Группа"
        for group in user_groups:
            if group['group_id'] == group_id:
                group_name = group['group_name']
                break
        
        # Проверяем, есть ли уже чаты в группе
        chats = self.db.get_group_vk_chats(group_id)
        
        if chats:
            # Если чаты есть, проверяем количество
            if len(chats) == 1:
                # Если только один чат, автоматически переходим к нему
                chat_id = chats[0]['chat_id']
                chat_name = chats[0].get('chat_name', f'Чат {chat_id}')
                
                # Показываем сообщение о автоматическом выборе
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    f"✅ Выбрана группа: {group_name}\n\n"
                    f"🎯 Автоматически выбран единственный чат: {chat_name}\n"
                    f"⏳ Загружаем информацию...",
                    reply_markup=None
                )
                
                # Небольшая задержка для лучшего UX
                await asyncio.sleep(1)
                
                await self._handle_chat_selection(update, context, chat_id)
            else:
                # Если несколько чатов, показываем их список
                keyboard = chat_list_keyboard(chats)
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    f"✅ Выбрана группа: {group_name}\n\n"
                    f"📋 Список чатов VK MAX:",
                    reply_markup=keyboard
                )
        else:
            # Если чатов нет, показываем меню управления
            keyboard = chat_management_keyboard()
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"✅ Выбрана группа: {group_name}\n\n"
                f"📊 Управление чатами VK MAX\n\n"
                f"Чаты не добавлены. Добавьте первый чат:",
                reply_markup=keyboard
            )
    
    async def _handle_add_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка добавления чата"""
        keyboard = chat_add_method_keyboard()
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "➕ Добавить чат VK MAX\n\n"
            "Выберите способ добавления чата:",
            reply_markup=keyboard
        )
    
    async def _handle_select_from_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора чата из списка"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "📋 Загружаем список доступных чатов...\n\n"
            "Это может занять несколько секунд.",
            reply_markup=cancel_keyboard()
        )
        
        try:
            # Подключаемся к VK MAX
            if not await self.vk.connect():
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    "❌ Ошибка подключения к VK MAX",
                    reply_markup=back_keyboard()
                )
                return
            
            # Получаем список доступных чатов
            available_chats = await self.vk.get_available_chats()
            await self.vk.disconnect()
            
            if not available_chats:
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    "❌ Не удалось получить список чатов\n\n"
                    "Попробуйте ввести ID чата вручную.",
                    reply_markup=chat_add_method_keyboard()
                )
                return
            
            # Сохраняем список чатов в контексте
            context.user_data['available_chats'] = available_chats
            context.user_data['chats_page'] = 0
            
            # Показываем первую страницу
            keyboard = available_chats_keyboard(available_chats, 0)
            total_chats = len(available_chats)
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"📋 Доступные чаты VK MAX ({total_chats} чатов):\n\n"
                "Выберите чат для добавления:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка получения списка чатов: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=chat_add_method_keyboard()
            )
    
    async def _handle_enter_chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ID чата вручную"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "🔍 Ввод ID чата VK MAX\n\n"
            "Введите ID чата VK MAX:",
            reply_markup=cancel_keyboard()
        )
        
        # Устанавливаем состояние ожидания ID чата
        context.user_data['waiting_for_chat_id'] = True
    
    async def _handle_select_available_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка выбора чата из списка"""
        user = update.effective_user
        group_id = context.user_data.get('selected_group_id')
        
        if not group_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        try:
            # Находим информацию о выбранном чате
            available_chats = context.user_data.get('available_chats', [])
            selected_chat = None
            
            for chat in available_chats:
                if str(chat['id']) == str(chat_id):
                    selected_chat = chat
                    break
            
            if not selected_chat:
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    "❌ Чат не найден в списке",
                    reply_markup=back_keyboard()
                )
                return
            
            # Добавляем чат в БД
            self.db.add_vk_chat(chat_id, selected_chat['title'], selected_chat['type'])
            self.db.add_group_vk_chat(group_id, chat_id, user.id)
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"✅ Чат '{selected_chat['title']}' добавлен\n\n"
                f"👥 Участников: {selected_chat['participants_count']}\n"
                f"🆔 ID: {chat_id}",
                reply_markup=chat_management_keyboard()
            )
            
            # Очищаем данные из контекста
            context.user_data.pop('available_chats', None)
            context.user_data.pop('chats_page', None)
            
        except Exception as e:
            logger.error(f"Ошибка добавления чата: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_keyboard()
            )
    
    async def _handle_chats_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
        """Обработка переключения страниц списка чатов"""
        available_chats = context.user_data.get('available_chats', [])
        
        if not available_chats:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Список чатов не найден",
                reply_markup=chat_add_method_keyboard()
            )
            return
        
        # Обновляем номер страницы
        context.user_data['chats_page'] = page
        
        # Показываем страницу
        keyboard = available_chats_keyboard(available_chats, page)
        total_chats = len(available_chats)
        
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            f"📋 Доступные чаты VK MAX ({total_chats} чатов):\n\n"
            "Выберите чат для добавления:",
            reply_markup=keyboard
        )
    
    async def _handle_search_chat_by_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка поиска чата по ID"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "🔍 Поиск чата по ID\n\n"
            "Введите ID чата VK MAX:",
            reply_markup=cancel_keyboard()
        )
        
        # Устанавливаем состояние ожидания ID чата
        context.user_data['waiting_for_chat_id'] = True
    
    async def _handle_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, date: str):
        """Обработка выбора даты для анализа"""
        chat_id = context.user_data.get('selected_chat_id')
        
        if not chat_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Чат не выбран",
                reply_markup=back_keyboard()
            )
            return
        
        # Проверяем, есть ли уже суммаризация за эту дату
        existing_summary = self.db.get_summary(chat_id, date)
        
        if existing_summary:
            # Если суммаризация уже есть, предлагаем выбор
            keyboard = [
                [InlineKeyboardButton("🔄 Сгенерировать новую", callback_data=f"generate_new_summary_{chat_id}_{date}")],
                [InlineKeyboardButton("👁️ Посмотреть последнюю", callback_data=f"view_existing_summary_{chat_id}_{date}")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")]
            ]
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"📊 Суммаризация за {date} уже существует\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Сохраняем выбранную дату в контексте
        context.user_data['selected_date'] = date
        
        # Показываем выбор модели для анализа
        await self.select_model_for_analysis_handler(update, context)
    
    async def _handle_list_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка списка чатов"""
        group_id = context.user_data.get('selected_group_id')
        if not group_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        chats = self.db.get_group_vk_chats(group_id)
        
        if not chats:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "📋 Список чатов пуст\n\n"
                "Добавьте чат с помощью кнопки '➕ Добавить чат'",
                reply_markup=chat_management_keyboard()
            )
            return
        
        keyboard = chat_list_keyboard(chats)
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "📋 Список чатов VK MAX:",
            reply_markup=keyboard
        )
    
    async def _handle_chat_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка выбора чата"""
        context.user_data['selected_chat_id'] = chat_id
        
        # Получаем статистику чата
        stats = self.db.get_chat_stats(chat_id)
        
        text = f"💬 Чат: {chat_id}\n\n"
        text += f"📊 *Статистика:*\n"
        text += f"• Всего сообщений: {stats['total_messages']}\n"
        text += f"• Дней загружено: {stats['days_count']}\n\n"
        
        if stats['recent_days']:
            text += "📅 *Последние дни:*\n"
            for day in stats['recent_days'][:5]:
                text += f"• {day['date']} ({day['count']} сообщений)\n"
        
        keyboard = chat_settings_keyboard(chat_id)
        await TelegramMessageSender.safe_edit_message_text(
            update.callback_query,
            text,
            reply_markup=keyboard
        )
    
    async def _handle_chat_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка статистики чата"""
        stats = self.db.get_chat_stats(chat_id)
        
        text = f"📊 Статистика чата {chat_id}\n\n"
        text += f"• Всего сообщений: {stats['total_messages']}\n"
        text += f"• Дней загружено: {stats['days_count']}\n\n"
        
        if stats['recent_days']:
            text += "📅 *Последние дни:*\n"
            for day in stats['recent_days']:
                text += f"• {day['date']} ({day['count']} сообщений)\n"
        
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            text,
            reply_markup=back_keyboard()
        )
    
    async def _handle_load_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка загрузки сообщений"""
        # Проверяем, есть ли уже сообщения в чате
        last_timestamp = self.db.get_last_message_timestamp(chat_id)
        
        if last_timestamp:
            # Если сообщения уже есть, предлагаем загрузить только новые
            keyboard = [
                [InlineKeyboardButton("🔄 Загрузить только новые", callback_data=f"load_new_messages_{chat_id}")],
                [InlineKeyboardButton("🔄 Загрузить все заново", callback_data=f"load_all_messages_{chat_id}")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")]
            ]
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"📊 В чате уже есть сообщения\n\n"
                f"Последнее сообщение: {datetime.fromtimestamp(last_timestamp/1000).strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Выберите тип загрузки:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Если сообщений нет, загружаем все
            await self._load_messages_worker(update, context, chat_id, load_only_new=False)
    
    async def _load_messages_worker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str, load_only_new: bool = False):
        """Рабочий метод загрузки сообщений"""
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            f"🔄 {'Загружаем новые сообщения' if load_only_new else 'Загружаем сообщения'}...\n\n"
            "Это может занять некоторое время.",
            reply_markup=cancel_keyboard()
        )
        
        try:
            # Подключаемся к VK MAX
            if not await self.vk.connect():
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    "❌ Ошибка подключения к VK MAX",
                    reply_markup=back_keyboard()
                )
                return
            
            # Загружаем сообщения
            messages = await self.vk.load_chat_messages(chat_id, db_manager=self.db, load_only_new=load_only_new)
            
            if not messages:
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    f"❌ {'Нет новых сообщений' if load_only_new else 'Не удалось загрузить сообщения'}",
                    reply_markup=back_keyboard()
                )
                return
            
            # Сохраняем в БД
            await self.vk.save_messages_to_db(self.db, chat_id, messages)
            
            message_type = "новых" if load_only_new else ""
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"✅ Загружено {len(messages)} {message_type} сообщений",
                reply_markup=back_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка загрузки сообщений: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_keyboard()
            )
        finally:
            await self.vk.disconnect()
    
    async def _handle_check_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка проверки суммаризации"""
        # Получаем последние дни
        stats = self.db.get_chat_stats(chat_id)
        
        if not stats['recent_days']:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Нет данных для анализа",
                reply_markup=back_keyboard()
            )
            return
        
        # Показываем выбор даты
        keyboard = date_selection_keyboard(stats['recent_days'])
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "📋 Выберите дату для анализа:",
            reply_markup=keyboard
        )
    
    async def _handle_publish_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
        """Обработка публикации суммаризации (выбор из доступных)"""
        # Получаем список доступных суммаризаций
        summaries = self.db.get_available_summaries(chat_id)
        
        if not summaries:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"📤 Публикация суммаризации\n\n"
                f"❌ Нет доступных суммаризаций для чата {chat_id}\n\n"
                f"Сначала создайте суммаризацию через '📋 Проверить суммаризацию'",
                reply_markup=back_keyboard()
            )
            return
        
        # Показываем список доступных суммаризаций
        keyboard = []
        for summary in summaries:
            date = summary['date']
            keyboard.append([InlineKeyboardButton(
                f"📅 {date}", 
                callback_data=f"publish_summary_{chat_id}_{date}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")])
        
        text = f"📤 *Публикация суммаризации*\n\n"
        text += f"📊 Доступные суммаризации для чата {chat_id}:\n\n"
        text += f"Выберите дату для публикации:"
        
        await TelegramMessageSender.safe_edit_message_text(
            update.callback_query,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_publish_summary_with_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str, date: str):
        """Обработка публикации суммаризации с датой"""
        group_id = context.user_data.get('selected_group_id')
        
        if not group_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        try:
            # Импортируем TelegramFormatter для умного экранирования
            from telegram_formatter import TelegramFormatter
            
            # Получаем суммаризацию из БД
            summary = self.db.get_summary(chat_id, date)
            
            if not summary:
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    f"❌ Суммаризация за {date} не найдена\n\n"
                    "Сначала создайте суммаризацию для этой даты.",
                    reply_markup=back_keyboard()
                )
                return
            
            # Получаем название чата из БД
            chat_info = self.db.get_vk_chat_info(chat_id)
            chat_name = chat_info.get('chat_name', f'Чат {chat_id}') if chat_info else f'Чат {chat_id}'
            
            # Форматируем сообщение для публикации
            from utils import format_summary_for_telegram
            
            logger.info(f"📝 Текст из БД для публикации: {summary[:200]}...")
            
            # Разбиваем на части если нужно
            message_parts = format_summary_for_telegram(summary, date, chat_name)
            
            logger.info(f"📝 Отформатированные части для публикации: {len(message_parts)} частей")
            logger.info(f"📝 Первая часть: {message_parts[0][:200]}...")
            
            # Проверяем права бота в группе
            try:
                chat_info = await context.bot.get_chat(group_id)
                logger.info(f"📋 Информация о группе: {chat_info.title} (ID: {group_id})")
                
                # Проверяем, является ли бот администратором
                bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
                logger.info(f"🤖 Статус бота в группе: {bot_member.status}")
                
            except Exception as e:
                logger.error(f"❌ Ошибка получения информации о группе: {e}")
            
            # Отправляем в группу
            logger.info(f"📤 Публикуем суммаризацию в группу {group_id} для чата {chat_id} за {date}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"📤 Публикуем суммаризацию в группу...\n\n"
                f"Чат: {chat_id}\n"
                f"Дата: {date}\n"
                f"Группа: {group_id}",
                reply_markup=cancel_keyboard()
            )
            
            # Проверяем, есть ли уже опубликованные сообщения для этой даты
            existing_message_ids = []
            for i in range(len(message_parts)):
                message_id = self.db.get_group_message(group_id, chat_id, f"{date}_{i}")
                if message_id:
                    existing_message_ids.append(message_id)
                else:
                    existing_message_ids.append(None)
            
            # Отправляем или обновляем сообщения в группе
            sent_message_ids = []
            for i, part in enumerate(message_parts):
                try:
                    if existing_message_ids[i]:
                        # Обновляем существующее сообщение
                        try:
                            logger.info(f"🔄 Обновляем сообщение {i+1} (ID: {existing_message_ids[i]}) в группе {group_id}")
                            # Применяем умное экранирование для MarkdownV2
                            escaped_part = TelegramFormatter.smart_escape_markdown_v2(part)
                            await context.bot.edit_message_text(
                                chat_id=group_id,
                                message_id=existing_message_ids[i],
                                text=escaped_part,
                                parse_mode=ParseMode.MARKDOWN_V2
                            )
                        except Exception as e:
                            logger.error(f"❌ Ошибка при обновлении сообщения {existing_message_ids[i]}: {e}")
                            if "can't parse entities" in str(e).lower():
                                # Fallback to plain text
                                await context.bot.edit_message_text(
                                    chat_id=group_id,
                                    message_id=existing_message_ids[i],
                                    text=part
                                )
                            elif "message to edit not found" in str(e).lower() or "bad request" in str(e).lower() or "message not found" in str(e).lower():
                                # Сообщение было удалено, отправляем новое
                                logger.warning(f"⚠️ Сообщение {existing_message_ids[i]} было удалено, отправляем новое")
                                logger.info(f"🔍 Текст ошибки: '{str(e)}'")
                                try:
                                    # Применяем умное экранирование для MarkdownV2
                                    from telegram_formatter import TelegramFormatter
                                    escaped_part = TelegramFormatter.smart_escape_markdown_v2(part)
                                    message = await context.bot.send_message(
                                        chat_id=group_id,
                                        text=escaped_part,
                                        parse_mode=ParseMode.MARKDOWN_V2,
                                        disable_notification=True
                                    )
                                    sent_message_ids.append(message.message_id)
                                    logger.info(f"✅ Отправлено новое сообщение {i+1} (ID: {message.message_id}) вместо удаленного")
                                except Exception as send_e:
                                    if "can't parse entities" in str(send_e).lower():
                                        # Fallback to plain text
                                        message = await context.bot.send_message(
                                            chat_id=group_id,
                                            text=part,
                                            disable_notification=True
                                        )
                                        sent_message_ids.append(message.message_id)
                                        logger.info(f"✅ Отправлено новое сообщение {i+1} (ID: {message.message_id}) в plain text вместо удаленного")
                                    else:
                                        logger.error(f"❌ Ошибка отправки нового сообщения вместо удаленного: {send_e}")
                                        break
                            else:
                                raise e
                        # Добавляем ID только если сообщение было успешно обновлено (не удалено)
                        if existing_message_ids[i] not in sent_message_ids:
                            sent_message_ids.append(existing_message_ids[i])
                            logger.info(f"✅ Обновлено сообщение {i+1} (ID: {existing_message_ids[i]})")
                    else:
                        # Отправляем новое сообщение
                        try:
                            logger.info(f"📤 Отправляем новое сообщение {i+1} в группу {group_id}")
                            # Применяем умное экранирование для MarkdownV2
                            escaped_part = TelegramFormatter.smart_escape_markdown_v2(part)
                            message = await context.bot.send_message(
                                chat_id=group_id,
                                text=escaped_part,
                                parse_mode=ParseMode.MARKDOWN_V2,
                                disable_notification=True
                            )
                        except Exception as e:
                            if "can't parse entities" in str(e).lower():
                                # Fallback to plain text
                                message = await context.bot.send_message(
                                    chat_id=group_id,
                                    text=part,
                                    disable_notification=True
                                )
                            else:
                                raise e
                        sent_message_ids.append(message.message_id)
                        logger.info(f"✅ Отправлено новое сообщение {i+1} (ID: {message.message_id})")
                    
                    if i < len(message_parts) - 1:
                        await asyncio.sleep(0.5)  # Пауза между сообщениями
                except Exception as e:
                    logger.error(f"Ошибка обработки сообщения {i+1}: {e}")
                    
                    # Проверяем, не является ли это ошибкой удаленного сообщения
                    if "message to edit not found" in str(e).lower() or "bad request" in str(e).lower() or "message not found" in str(e).lower():
                        logger.warning(f"⚠️ Сообщение было удалено, пытаемся отправить новое")
                        try:
                            # Отправляем новое сообщение
                            message = await context.bot.send_message(
                                chat_id=group_id,
                                text=part,
                                parse_mode=ParseMode.MARKDOWN_V2,
                                disable_notification=True
                            )
                            sent_message_ids.append(message.message_id)
                            logger.info(f"✅ Отправлено новое сообщение {i+1} (ID: {message.message_id}) вместо удаленного")
                        except Exception as send_e:
                            logger.error(f"❌ Не удалось отправить новое сообщение: {send_e}")
                    
                    # Продолжаем с следующим сообщением
                    continue
            
            # Сохраняем message_id в БД для каждой части
            for i, message_id in enumerate(sent_message_ids):
                if message_id:
                    self.db.update_group_message(group_id, chat_id, f"{date}_{i}", message_id)
            
            # Очищаем записи о сообщениях, которые больше не существуют
            for i, existing_id in enumerate(existing_message_ids):
                if existing_id and existing_id not in sent_message_ids:
                    logger.info(f"🗑️ Очищаем запись о несуществующем сообщении {existing_id}")
                    self.db.delete_group_message(group_id, chat_id, f"{date}_{i}")
            
            # Подсчитываем статистику
            updated_count = sum(1 for msg_id in existing_message_ids if msg_id is not None)
            new_count = len(sent_message_ids) - updated_count
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"✅ Суммаризация опубликована в группу!\n\n"
                f"📊 Чат: {chat_id}\n"
                f"📅 Дата: {date}\n"
                f"📝 Частей: {len(message_parts)}\n"
                f"🔄 Обновлено: {updated_count}\n"
                f"➕ Новых: {new_count}",
                reply_markup=back_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка публикации суммаризации: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"❌ Ошибка публикации: {str(e)}",
                reply_markup=back_keyboard()
            )
    
    async def _handle_back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка возврата в главное меню"""
        keyboard = main_menu_keyboard()
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "🏠 Главное меню\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    
    async def _handle_change_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка смены группы"""
        # Получаем все группы, где есть бот
        all_groups = self.db.get_all_groups()
        
        if not all_groups:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Нет доступных групп\n\n"
                "Для работы с ботом добавьте его в группу и сделайте администратором.",
                reply_markup=back_keyboard()
            )
            return
        
        # Показываем выбор группы
        keyboard = group_selection_keyboard(all_groups)
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "🔄 Смена группы\n\n"
            "Выберите группу для работы:",
            reply_markup=keyboard
        )
    
    async def _handle_back_to_manage_chats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка возврата к управлению чатами"""
        group_id = context.user_data.get('selected_group_id')
        if not group_id:
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        # Проверяем, есть ли уже чаты в группе
        chats = self.db.get_group_vk_chats(group_id)
        
        if chats:
            # Если чаты есть, сразу показываем их список
            keyboard = chat_list_keyboard(chats)
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "📋 Список чатов VK MAX:",
                reply_markup=keyboard
            )
        else:
            # Если чатов нет, показываем меню управления
            keyboard = chat_management_keyboard()
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                "📊 Управление чатами VK MAX\n\n"
                "Чаты не добавлены. Добавьте первый чат:",
                reply_markup=keyboard
            )
    
    async def _handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка отмены"""
        # Очищаем состояние
        context.user_data.pop('waiting_for_chat_id', None)
        context.user_data.pop('selected_chat_id', None)
        context.user_data.pop('available_chats', None)
        context.user_data.pop('chats_page', None)
        
        keyboard = main_menu_keyboard()
        await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
            "❌ Операция отменена\n\n"
            "Выберите действие:",
            reply_markup=keyboard
        )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        if context.user_data.get('waiting_for_chat_id'):
            await self._handle_chat_id_input(update, context)
        else:
            await update.message.reply_text(
                "Используйте кнопки для навигации или команду /start"
            )
    
    async def _handle_chat_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ID чата"""
        chat_id = update.message.text.strip()
        user = update.effective_user
        group_id = context.user_data.get('selected_group_id')
        
        if not group_id:
            await update.message.reply_text(
                "❌ Группа не выбрана",
                reply_markup=back_keyboard()
            )
            return
        
        try:
            # Проверяем доступ к чату
            if not await self.vk.connect():
                await update.message.reply_text(
                    "❌ Ошибка подключения к VK MAX",
                    reply_markup=back_keyboard()
                )
                return
            
            chat_info = await self.vk.get_chat_info(chat_id)
            await self.vk.disconnect()
            
            if not chat_info:
                await update.message.reply_text(
                    f"❌ Чат {chat_id} не найден или недоступен",
                    reply_markup=back_keyboard()
                )
                return
            
            # Добавляем чат в БД
            self.db.add_vk_chat(chat_id, chat_info['title'], chat_info['type'])
            self.db.add_group_vk_chat(group_id, chat_id, user.id)
            
            await update.message.reply_text(
                f"✅ Чат '{chat_info['title']}' добавлен",
                reply_markup=chat_management_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Ошибка добавления чата: {e}")
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_keyboard()
            )
        finally:
            # Очищаем состояние
            context.user_data.pop('waiting_for_chat_id', None)
    
    async def _handle_generate_new_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str, date: str):
        """Обработка генерации новой суммаризации"""
        # Сохраняем выбранную дату и chat_id в контексте
        context.user_data['selected_date'] = date
        context.user_data['selected_chat_id'] = chat_id
        
        # Показываем выбор модели для анализа
        await self.select_model_for_analysis_handler(update, context)
    
    async def _handle_improve_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str, date: str):
        """Обработка улучшения суммаризации на основе рефлексии"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем существующую суммаризацию
            existing_summary = self.db.get_summary(chat_id, date)
            if not existing_summary:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Суммаризация не найдена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                return
            
            # Показываем сообщение о начале улучшения
            await TelegramMessageSender.safe_edit_message_text(
                query,
                "✨ Улучшаем суммаризацию на основе рефлексии...\n\n⏳ Это может занять некоторое время.",
                reply_markup=cancel_keyboard()
            )
            
            # Получаем сообщения и контекст
            messages = self.db.get_messages_by_date(chat_id, date)
            if not messages:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Нет сообщений для улучшения",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                return
            
            # Извлекаем исходную суммаризацию и рефлексию из существующего результата
            if "🤔 Рефлексия и улучшения:" in existing_summary:
                parts = existing_summary.split("🤔 Рефлексия и улучшения:")
                original_summary = parts[0].replace("📝 **Резюме:**\n", "").replace("**📝 Исходная суммаризация:**\n", "").strip()
                reflection = parts[1].strip()
            elif "🤔 Рефлексия и анализ:" in existing_summary:
                parts = existing_summary.split("🤔 Рефлексия и анализ:")
                original_summary = parts[0].replace("📝 **Резюме:**\n", "").replace("**📝 Исходная суммаризация:**\n", "").strip()
                reflection = parts[1].strip()
            else:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Не найдена рефлексия для улучшения",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                return
            
            # Определяем провайдера из контекста
            selected_provider = context.user_data.get('selected_analysis_provider', 'gigachat')
            selected_model = context.user_data.get('selected_analysis_model')
            
            # Создаем провайдера
            provider = self.analyzer.provider_factory.create_provider(selected_provider, self.analyzer.config)
            if not provider:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Не удалось создать провайдер: {selected_provider}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                return
            
            # Инициализируем провайдера
            if not await provider.initialize():
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Не удалось инициализировать провайдер: {selected_provider}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                return
            
            # Создаем контекст чата
            chat_context = {
                'total_messages': len(messages),
                'date': date,
                'provider': selected_provider,
                'model': selected_model
            }
            
            # Улучшаем суммаризацию
            improved_summary = await self.analyzer.improve_summary_with_reflection(
                provider, original_summary, reflection, messages, chat_context
            )
            
            if improved_summary:
                # Сохраняем улучшенную суммаризацию
                self.db.save_summary(chat_id, date, improved_summary)
                
                # Показываем результат (HTML для устойчивого рендеринга)
                text = f"📊 <b>Полный анализ чата за {TelegramFormatter.escape_html(date)}</b>\n\n"
                text += f"📈 <b>Статистика:</b>\n"
                text += f"• Сообщений: {len(messages)}\n"
                text += f"• Дата: {TelegramFormatter.escape_html(date)}\n"
                text += f"• Модель: {TelegramFormatter.escape_html(selected_provider)}\n"
                if selected_model:
                    text += f"• Модель: {TelegramFormatter.escape_html(selected_model)}\n"
                # Экранируем тексты для безопасного отображения в HTML
                html_original = TelegramFormatter.escape_html(original_summary)
                html_reflection = TelegramFormatter.escape_html(reflection)
                html_improved = TelegramFormatter.escape_html(improved_summary)
                
                text += f"\n{html_improved}"
                
                keyboard = [
                    [InlineKeyboardButton("📤 Вывести в группу", callback_data=f"publish_summary_{chat_id}_{date}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")]
                ]
                
                await TelegramMessageSender.safe_edit_message_text(
                    query,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.HTML
                )
            else:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Не удалось улучшить суммаризацию",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                    ]])
                )
                
        except Exception as e:
            logger.error(f"Ошибка улучшения суммаризации: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                "❌ Произошла ошибка при улучшении суммаризации",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")
                ]])
            )
    
    async def _handle_view_existing_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str, date: str):
        """Обработка просмотра существующей суммаризации"""
        try:
            # Получаем существующую суммаризацию
            summary = self.db.get_summary(chat_id, date)
            
            if not summary:
                await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                    f"❌ Суммаризация за {date} не найдена",
                    reply_markup=back_keyboard()
                )
                return
            
            # Получаем статистику для отображения
            messages = self.db.get_messages_by_date(chat_id, date)
            
            # Показываем существующую суммаризацию
            text = f"📊 *Существующая суммаризация за {date}*\n\n"
            text += f"📈 *Статистика:*\n"
            text += f"• Сообщений: {len(messages) if messages else 0}\n"
            text += f"• Дата: {date}\n\n"
            text += f"📝 *Резюме:*\n{summary}"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Сгенерировать новую", callback_data=f"generate_new_summary_{chat_id}_{date}")],
                [InlineKeyboardButton("📤 Вывести в группу", callback_data=f"publish_summary_{chat_id}_{date}")],
                [InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")]
            ]
            
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Ошибка просмотра существующей суммаризации: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                update.callback_query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=back_keyboard()
            )
    
    # AI Provider Handlers
    async def ai_provider_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора AI провайдера"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем все провайдеры (включая недоступные)
            available_providers = await self.analyzer.get_available_providers()
            provider_names = [p['name'] for p in available_providers]
            
            if not provider_names:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Нет зарегистрированных AI провайдеров.\n\n"
                    "Проверьте настройки API ключей в конфигурации.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_management")
                    ]])
                )
                return
            
            # Получаем текущие предпочтения пользователя
            user_id = update.effective_user.id
            user_preferences = self.db.get_user_ai_preference(user_id)
            current_provider = user_preferences.get('default_provider', 'gigachat') if user_preferences else 'gigachat'
            
            keyboard = ai_provider_selection_keyboard(provider_names, current_provider, available_providers)
            
            text = "🤖 Выберите AI модель для суммаризации:\n\n"
            for provider in available_providers:
                status = "✅ Доступен" if provider.get('available', False) else "❌ Недоступен"
                text += f"• {provider['display_name']}: {status}\n"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора AI провайдера: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_management")
                ]])
            )
    
    async def select_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретного провайдера"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(":")[1]
            user_id = update.effective_user.id
            
            # Проверяем доступность провайдера
            provider_info = self.analyzer.get_provider_info(provider_name)
            if not provider_info:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Провайдер {provider_name} не найден",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                    ]])
                )
                return
            
            # Проверяем сохраненный статус доступности провайдера
            availability_stats = self.db.get_provider_availability(provider_name)
            if availability_stats and not availability_stats.get('is_available', True):
                display_name = provider_info.get('display_name', provider_name.title())
                await TelegramMessageSender.safe_edit_message_text(
                    query,
                    f"❌ Провайдер **{display_name}** недоступен\n\n"
                    f"Последняя проверка: {availability_stats.get('last_check', 'Неизвестно')}\n"
                    f"Количество ошибок: {availability_stats.get('error_count', 0)}\n\n"
                    f"Используйте кнопку '🔍 Проверить доступность' для повторной проверки.\n\n"
                    f"Описание: {provider_info.get('description', 'Нет описания')}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔍 Проверить доступность", callback_data="check_providers_availability"),
                        InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                    ]])
                )
                return
            
            # Если выбран OpenRouter, показываем выбор моделей
            if provider_name == 'openrouter':
                await self.openrouter_model_selection_handler(update, context)
                return
            
            # Обновляем предпочтения пользователя
            self.db.add_user_ai_preference(user_id, provider_name)
            
            # Получаем информацию о провайдере
            provider_info = self.analyzer.get_provider_info(provider_name)
            display_name = provider_info.get('display_name', provider_name.title()) if provider_info else provider_name.title()
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"✅ Выбрана модель: {display_name}\n\n"
                f"Теперь при суммаризации будет использоваться эта модель.\n\n"
                f"📝 Описание: {provider_info.get('description', 'Нет описания') if provider_info else 'Нет описания'}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад к управлению чатами", callback_data="back_to_chat_management")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора провайдера: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                ]])
            )
    
    async def ai_provider_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик просмотра статуса AI провайдеров"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем статус всех провайдеров
            available_providers = await self.analyzer.get_available_providers()
            
            text = "📊 Статус AI провайдеров:\n\n"
            
            for provider in available_providers:
                status_icon = "✅" if provider.get('available', False) else "❌"
                status_text = "Доступен" if provider.get('available', False) else "Недоступен"
                
                text += f"{status_icon} *{provider['display_name']}*\n"
                text += f"   Статус: {status_text}\n"
                text += f"   Описание: {provider.get('description', 'Нет описания')}\n"
                text += f"   Версия: {provider.get('version', 'Неизвестно')}\n\n"
            
            # Получаем статистику из базы данных
            availability_stats = self.db.get_provider_availability()
            if availability_stats:
                text += "📈 Статистика использования:\n"
                for provider_name, stats in availability_stats.items():
                    text += f"• {provider_name}: {stats.get('error_count', 0)} ошибок\n"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Обновить", callback_data="ai_provider_status"),
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка просмотра статуса провайдеров: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")
                ]])
            )
    
    async def check_providers_availability_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик проверки доступности всех провайдеров"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Показываем сообщение о начале проверки
            await TelegramMessageSender.safe_edit_message_text(
                query,
                "🔍 Проверяем доступность всех провайдеров...\n\n⏳ Это может занять некоторое время.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Отмена", callback_data="ai_provider_settings")
                ]])
            )
            
            # Тестируем все провайдеры
            test_results = await self.analyzer.test_all_providers()
            
            # Формируем результат
            text = "🧪 Результаты проверки доступности провайдеров:\n\n"
            
            for provider_name, is_available in test_results.items():
                status_icon = "✅" if is_available else "❌"
                provider_info = self.analyzer.get_provider_info(provider_name)
                display_name = provider_info.get('display_name', provider_name.title()) if provider_info else provider_name.title()
                
                text += f"{status_icon} *{display_name}*\n"
                if not is_available:
                    text += f"   ⚠️ Провайдер недоступен\n"
                text += "\n"
            
            # Обновляем статус в базе данных
            for provider_name, is_available in test_results.items():
                self.db.update_provider_availability(provider_name, is_available)
            
            text += "💾 Статус сохранен в базе данных."
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Проверить снова", callback_data="check_providers_availability"),
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка проверки доступности провайдеров: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка при проверке: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")
                ]])
            )
    
    async def ai_provider_defaults_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек провайдера по умолчанию"""
        query = update.callback_query
        await query.answer()
        
        try:
            user_id = update.effective_user.id
            user_preferences = self.db.get_user_ai_preference(user_id)
            current_default = user_preferences.get('default_provider', 'gigachat') if user_preferences else 'gigachat'
            
            keyboard = ai_provider_defaults_keyboard(current_default)
            
            text = f"⚙️ Настройки AI провайдера по умолчанию\n\n"
            text += f"Текущий провайдер: *{current_default.title()}*\n\n"
            text += "Выберите провайдер, который будет использоваться по умолчанию при суммаризации чатов."
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
            )
            
        except Exception as e:
            logger.error(f"Ошибка настроек провайдера по умолчанию: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_settings")
                ]])
            )
    
    async def set_default_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик установки провайдера по умолчанию"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(":")[1]
            user_id = update.effective_user.id
            
            # Обновляем предпочтения пользователя
            self.db.add_user_ai_preference(user_id, provider_name)
            
            # Получаем информацию о провайдере
            provider_info = self.analyzer.get_provider_info(provider_name)
            display_name = provider_info.get('display_name', provider_name.title()) if provider_info else provider_name.title()
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"✅ Провайдер по умолчанию изменен на: *{display_name}*\n\n"
                f"Теперь этот провайдер будет использоваться по умолчанию при суммаризации чатов.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад к настройкам", callback_data="ai_provider_settings")
                ]]),
            )
            
        except Exception as e:
            logger.error(f"Ошибка установки провайдера по умолчанию: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="ai_provider_defaults")
                ]])
            )
    
    # OpenRouter Model Handlers
    async def openrouter_model_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора модели OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем OpenRouter провайдер
            openrouter_provider = self.analyzer.provider_factory.create_provider('openrouter', self.analyzer.config)
            if not openrouter_provider:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ OpenRouter провайдер недоступен",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                    ]])
                )
                return
            
            # Получаем доступные модели
            available_models = await openrouter_provider.get_available_models()
            
            # Получаем текущую модель пользователя
            user_id = update.effective_user.id
            current_model = self.db.get_user_openrouter_model(user_id)
            
            keyboard = openrouter_model_selection_keyboard(available_models, current_model)
            
            text = "🔗 Выберите модель OpenRouter (топ 10 бесплатных):\n\n"
            for model_id, model_info in available_models.items():
                free_indicator = "🆓 Бесплатная" if model_info.get('free', False) else "💰 Платная"
                current_indicator = " (текущая)" if model_id == current_model else ""
                text += f"• *{model_info['display_name']}* {free_indicator}{current_indicator}\n"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора модели OpenRouter: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                ]])
            )
    
    async def select_openrouter_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретной модели OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(":")[1]
            
            # Получаем OpenRouter провайдер
            openrouter_provider = self.analyzer.provider_factory.create_provider('openrouter', self.analyzer.config)
            if not openrouter_provider:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ OpenRouter провайдер недоступен",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                    ]])
                )
                return
            
            # Получаем информацию о модели
            available_models = await openrouter_provider.get_available_models()
            model_info = available_models.get(model_id, {})
            
            if not model_info:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Модель не найдена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="openrouter_model_selection")
                    ]])
                )
                return
            
            keyboard = openrouter_model_info_keyboard(model_id)
            
            free_indicator = "🆓 Бесплатная" if model_info.get('free', False) else "💰 Платная"
            
            text = f"🔗 *{model_info['display_name']}*\n\n"
            text += f"📝 *Описание:* {model_info['description']}\n"
            text += f"💰 *Тип:* {free_indicator}\n"
            text += f"🆔 *ID модели:* `{model_id}`\n\n"
            text += "Вы хотите использовать эту модель для суммаризации?"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора модели OpenRouter: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="openrouter_model_selection")
                ]])
            )
    
    async def confirm_openrouter_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения выбора модели OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(":")[1]
            user_id = update.effective_user.id
            
            # Сохраняем выбранную модель
            self.db.set_user_openrouter_model(user_id, model_id)
            
            # Получаем информацию о модели
            openrouter_provider = self.analyzer.provider_factory.create_provider('openrouter', self.analyzer.config)
            if openrouter_provider:
                available_models = openrouter_provider.get_available_models()
                model_info = available_models.get(model_id, {})
                display_name = model_info.get('display_name', model_id)
            else:
                display_name = model_id
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"✅ Выбрана модель OpenRouter: **{display_name}**\n\n"
                f"Теперь при суммаризации через OpenRouter будет использоваться эта модель.\n\n"
                f"🆔 ID модели: `{model_id}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад к управлению чатами", callback_data="back_to_chat_management")
                ]]),
            )
            
        except Exception as e:
            logger.error(f"Ошибка подтверждения модели OpenRouter: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="openrouter_model_selection")
                ]])
            )
    
    # Model Selection for Analysis Handlers
    async def select_model_for_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора модели для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем все провайдеры с сохраненным статусом (без проверки доступности)
            available_providers = self.analyzer.get_providers_with_saved_status(self.db)
            provider_names = [p['name'] for p in available_providers]
            
            if not provider_names:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Нет зарегистрированных AI провайдеров для анализа",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_settings")
                    ]])
                )
                return
            
            # Создаем клавиатуру с доступными провайдерами
            keyboard = []
            for provider_name in provider_names:
                # Находим информацию о провайдере
                provider_info = None
                for p in available_providers:
                    if p['name'] == provider_name:
                        provider_info = p
                        break
                
                display_name = provider_info.get('display_name', provider_name.title()) if provider_info else provider_name.title()
                is_available = provider_info.get('available', False) if provider_info else False
                
                # Добавляем индикатор статуса
                if is_available:
                    status_icon = "✅"
                    status_text = "Доступен"
                else:
                    status_icon = "❌"
                    status_text = "Не проверен"
                
                keyboard.append([InlineKeyboardButton(
                    f"{status_icon} {display_name} ({status_text})",
                    callback_data=f"analyze_with_provider:{provider_name}"
                )])
            
            # Добавляем кнопку проверки доступности
            keyboard.append([InlineKeyboardButton("🔍 Проверить доступность", callback_data="check_providers_availability")])
            
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            date = context.user_data.get('selected_date')
            if date:
                # Если это генерация новой суммаризации, возвращаемся к выбору действия
                chat_id = context.user_data.get('selected_chat_id')
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")])
            else:
                # Если это обычный анализ, возвращаемся к настройкам чата
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_settings")])
            
            # Определяем контекст (новая суммаризация или обычный анализ)
            date = context.user_data.get('selected_date')
            if date:
                # Don't escape here - let telegram_message_sender handle it
                text = f"🤖 Выберите AI модель для анализа за {date}:\n\n"
            else:
                text = "🤖 Выберите AI модель для анализа:\n\n"
            
            text += "Эта модель будет использована только для текущего анализа.\n"
            text += "Ваши глобальные настройки не изменятся.\n\n"
            text += "ℹ️ *Статус провайдеров:*\n"
            text += "• ✅ Доступен - провайдер проверен и работает\n"
            text += "• ❌ Не проверен - требуется проверка доступности\n\n"
            
            # Format provider status with MarkdownV2, escaping reserved characters
            for provider in available_providers:
                status = '✅ Доступен' if provider.get('available', False) else '❌ Не проверен'
                # Don't escape here - let telegram_message_sender handle it
                provider_name = provider.get('display_name', 'Unknown Provider')
                text += f"• *{provider_name}*: {status}\n"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора модели для анализа: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="back_to_chat_settings")
                ]])
            )
    
    async def analyze_with_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик анализа с выбранным провайдером"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(":")[1]
            
            # Проверяем доступность провайдера
            provider_info = self.analyzer.get_provider_info(provider_name)
            if not provider_info:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Провайдер {provider_name} не найден",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_model_for_analysis")
                    ]])
                )
                return
            
            # Проверяем сохраненный статус доступности провайдера
            availability_stats = self.db.get_provider_availability(provider_name)
            if availability_stats and not availability_stats.get('is_available', True):
                display_name = provider_info.get('display_name', provider_name.title())
                # Экранируем все тексты для безопасного использования в MarkdownV2
                safe_display_name = TelegramMessageSender.format_text_for_markdown_v2(display_name)
                safe_description = TelegramMessageSender.format_text_for_markdown_v2(
                    provider_info.get('description', 'Нет описания')
                )
                safe_last_check = TelegramMessageSender.format_text_for_markdown_v2(
                    availability_stats.get('last_check', 'Неизвестно')
                )
                
                error_text = f"❌ Провайдер *{safe_display_name}* недоступен\n\n"
                error_text += f"Последняя проверка: {safe_last_check}\n"
                error_text += f"Количество ошибок: {availability_stats.get('error_count', 0)}\n\n"
                error_text += f"Используйте кнопку '🔍 Проверить доступность' для повторной проверки\\.\n\n"
                error_text += f"Описание: {safe_description}"
                
                await TelegramMessageSender.safe_edit_message_text(
                    query,
                    error_text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔍 Проверить доступность", callback_data="check_providers_availability"),
                        InlineKeyboardButton("🔙 Назад", callback_data="select_model_for_analysis")
                    ]]),
                )
                return
            
            # Если выбран OpenRouter, показываем выбор моделей
            if provider_name == 'openrouter':
                await self.analyze_with_openrouter_model_selection_handler(update, context)
                return
            
            # Для других провайдеров сразу запускаем анализ
            context.user_data['selected_analysis_provider'] = provider_name
            context.user_data['selected_analysis_model'] = None  # Нет модели для других провайдеров
            
            # Запускаем анализ с выбранной датой
            await self._run_analysis_with_selected_model(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка анализа с провайдером: {e}")
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            date = context.user_data.get('selected_date')
            if date:
                chat_id = context.user_data.get('selected_chat_id')
                back_callback = f"select_chat_{chat_id}"
            else:
                back_callback = "select_model_for_analysis"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                ]])
            )
    
    async def analyze_with_openrouter_model_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора модели OpenRouter для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Получаем OpenRouter провайдер
            openrouter_provider = self.analyzer.provider_factory.create_provider('openrouter', self.analyzer.config)
            if not openrouter_provider:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ OpenRouter провайдер недоступен",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_model_for_analysis")
                    ]])
                )
                return
            
            # Получаем доступные модели
            available_models = await openrouter_provider.get_available_models()
            
            keyboard = []
            # Преобразуем словарь в список для индексации
            models_list = list(available_models.items())
            for index, (model_id, model_info) in enumerate(models_list):
                display_name = model_info.get('display_name', model_id)
                free_indicator = "🆓" if model_info.get('free', False) else "💰"
                keyboard.append([InlineKeyboardButton(
                    f"{free_indicator} {display_name}",
                    callback_data=f"analyze_with_openrouter_model_index:{index}"
                )])
            
            # Сохраняем полные model_id в контексте пользователя
            context.user_data['openrouter_models_list'] = models_list
            
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            date = context.user_data.get('selected_date')
            if date:
                chat_id = context.user_data.get('selected_chat_id')
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")])
            else:
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="select_model_for_analysis")])
            
            text = "🔗 Выберите модель OpenRouter для анализа (топ 10 бесплатных):\n\n"
            text += "Эта модель будет использована только для текущего анализа.\n"
            text += "Ваши глобальные настройки не изменятся.\n\n"
            
            for model_id, model_info in available_models.items():
                free_indicator = "🆓 Бесплатная" if model_info.get('free', False) else "💰 Платная"
                text += f"• **{model_info['display_name']}** - {free_indicator}\n"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            
        except Exception as e:
            logger.error(f"Ошибка выбора модели OpenRouter для анализа: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="select_model_for_analysis")
                ]])
            )
    
    async def analyze_with_openrouter_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик анализа с выбранной моделью OpenRouter (старый формат)"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(":")[1]
            
            # Сохраняем выбранную модель для анализа
            context.user_data['selected_analysis_provider'] = 'openrouter'
            context.user_data['selected_analysis_model'] = model_id
            
            # Запускаем анализ с выбранной датой
            await self._run_analysis_with_selected_model(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка анализа с моделью OpenRouter: {e}")
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            date = context.user_data.get('selected_date')
            if date:
                chat_id = context.user_data.get('selected_chat_id')
                back_callback = f"select_chat_{chat_id}"
            else:
                back_callback = "select_model_for_analysis"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                ]])
            )
    
    async def _run_analysis_with_selected_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Запуск анализа с выбранной моделью и датой"""
        query = update.callback_query
        chat_id = context.user_data.get('selected_chat_id')
        date = context.user_data.get('selected_date')
        selected_provider = context.user_data.get('selected_analysis_provider')
        selected_model = context.user_data.get('selected_analysis_model')
        
        if not chat_id or not date:
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            if date:
                back_callback = f"select_chat_{chat_id}"
            else:
                back_callback = "back_to_chat_settings"
            
                await TelegramMessageSender.safe_edit_message_text(
                query,
                "❌ Ошибка: не выбраны чат или дата",
                    reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                    ]])
                )
                return
            
        # Показываем сообщение о начале анализа
        provider_info = self.analyzer.get_provider_info(selected_provider)
        display_name = provider_info.get('display_name', selected_provider.title()) if provider_info else selected_provider.title()
        
        analysis_text = f"🤖 Анализируем чат за {date}...\n\n"
        analysis_text += f"📊 Модель: *{display_name}*\n"
        if selected_model:
            analysis_text += f"🔗 Модель: *{selected_model}*\n"
        
        # Добавляем информацию о рефлексии
        # Убираем информацию о рефлексии из сообщения
        
        analysis_text += "\n\n⏳ Это может занять некоторое время."
        
        await TelegramMessageSender.safe_edit_message_text(
            query,
            analysis_text,
            reply_markup=cancel_keyboard()
        )
        
        try:
            # Получаем сообщения за выбранную дату
            messages = self.db.get_messages_by_date(chat_id, date)
            
            if not messages:
                # Определяем правильную кнопку "Назад" в зависимости от контекста
                if date:
                    back_callback = f"select_chat_{chat_id}"
                else:
                    back_callback = "back_to_chat_settings"
                
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Нет сообщений за {date}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                    ]])
                )
                return
            
            # Анализируем сообщения с выбранной моделью
            summary = await self.analyzer.analyze_chat_with_specific_model(
                messages, selected_provider, selected_model, update.effective_user.id
            )
            
            # Очищаем временные настройки
            context.user_data.pop('selected_analysis_provider', None)
            context.user_data.pop('selected_analysis_model', None)
            context.user_data.pop('selected_date', None)
            
            if summary:
                # Сохраняем суммаризацию в БД
                if isinstance(summary, dict):
                    # Новый формат с отдельными компонентами
                    self.db.save_summary(
                        chat_id, date, 
                        summary.get('summary', ''),
                        reflection_text=summary.get('reflection'),
                        improved_summary_text=summary.get('improved')
                    )
                    display_text = summary.get('display_text', summary.get('summary', ''))
                else:
                    # Старый формат - только текст
                    self.db.save_summary(chat_id, date, summary)
                    display_text = summary
                
                # Показываем результат с Markdown форматированием
                text = f"📊 *Анализ чата за {date}*\n\n"
                
                # Создаем статистику в виде blockquote
                stats_lines = [
                    "> 📈 *Статистика*",
                    f"> • Сообщений: {len(messages)}",
                    f"> • Дата: {date}",
                    f"> • Провайдер: {display_name}"
                ]
                if selected_model:
                    stats_lines.append(f"> • Модель: {selected_model}")
                
                text += "\n".join(stats_lines) + "\n\n"
                
                # Создаем клавиатуру заранее
                keyboard = [
                    [InlineKeyboardButton("📤 Вывести в группу", callback_data=f"publish_summary_{chat_id}_{date}")]
                ]
                
                # Форматируем результат анализа
                if isinstance(summary, dict):
                    # Используем новое форматирование с тремя разделами
                    formatted_result = TelegramFormatter.format_analysis_result_with_reflection(summary, "markdown_v2")
                    text += formatted_result
                else:
                    # Старый формат - просто текст
                    text += f"📝 *Резюме:*\n{display_text}"
                
                # Проверяем длину сообщения и разбиваем на части если нужно
                if len(text) > 4000:  # Оставляем запас для кнопок
                    logger.warning(f"⚠️ Сообщение слишком длинное ({len(text)} символов), разбиваем на части")
                    
                    # Разбиваем на части
                    message_parts = TelegramFormatter.split_long_message(text, 4000, "markdown")
                    
                    # Отправляем первую часть с кнопками
                    await TelegramMessageSender.safe_edit_message_text(
                        query,
                        message_parts[0],
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                    
                    # Отправляем остальные части как новые сообщения
                    for i, part in enumerate(message_parts[1:], 1):
                        await query.message.reply_text(
                            part,
                            parse_mode="markdown_v2"
                        )
                    
                    return
                
                # Добавляем кнопку "Улучшить", если есть рефлексия
                logger.debug(f"=== CHECKING REFLECTION BUTTON ===")
                logger.debug(f"Summary type: {type(summary)}")
                
                has_reflection = False
                if isinstance(summary, dict):
                    has_reflection = summary.get('reflection') is not None
                    logger.debug(f"Dict format - has reflection: {has_reflection}")
                else:
                    has_reflection = "🤔 Рефлексия и улучшения:" in summary or "🤔 Рефлексия и анализ:" in summary
                    logger.debug(f"String format - has reflection: {has_reflection}")
                
                if has_reflection:
                    logger.debug("✅ Adding 'Улучшить на основе рефлексии' button")
                    keyboard.append([InlineKeyboardButton("✨ Улучшить на основе рефлексии", callback_data=f"improve_summary_{chat_id}_{date}")])
                else:
                    logger.debug("❌ No reflection found, not adding button")
                
                keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"select_chat_{chat_id}")])
                
                await TelegramMessageSender.safe_edit_message_text(
                    query,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                # Определяем правильную кнопку "Назад" в зависимости от контекста
                if date:
                    back_callback = f"select_chat_{chat_id}"
                else:
                    back_callback = "back_to_chat_settings"
                
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    f"❌ Не удалось проанализировать чат за {date}\n\n"
                    f"Попробуйте другую модель или проверьте настройки API.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                    ]])
                )
            
        except Exception as e:
            logger.error(f"Ошибка анализа чата: {e}")
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            if date:
                back_callback = f"select_chat_{chat_id}"
            else:
                back_callback = "back_to_chat_settings"
            
            # Безопасно экранируем текст ошибки для MarkdownV2
            safe_error_text = TelegramFormatter.escape_markdown_v2(str(e))
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка анализа: {safe_error_text}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                ]])
            )
    
    # Top-5 Models Handlers
    async def top5_models_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора топ-5 моделей"""
        query = update.callback_query
        
        try:
            # Загружаем конфигурацию топ-5 моделей
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(__file__), 'top5_models_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                top5_models = config.get('top5_models', [])
            else:
                top5_models = []
            
            if not top5_models:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Конфигурация топ-5 моделей не найдена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                    ]])
                )
                return
            
            # Создаем текст с описанием топ-5 моделей
            text = "🏆 <b>ТОП-5 ЛУЧШИХ МОДЕЛЕЙ</b>\n\n"
            text += "Выберите одну из лучших бесплатных моделей для суммаризации:\n\n"
            
            for i, model in enumerate(top5_models, 1):
                text += f"<b>{i}. {model['name']}</b>\n"
                text += f"   {model['description']}\n"
                text += f"   Контекст: {model['context_length']:,} токенов\n\n"
            
            text += "💡 <i>Рекомендуется: NVIDIA Nemotron Nano 9B v2 (быстрая и надежная)</i>"
            
            keyboard = top5_models_keyboard()
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Ошибка в top5_models_selection_handler: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка загрузки топ-5 моделей: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="select_ai_provider")
                ]])
            )
    
    async def top5_model_info_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, model_id: str):
        """Обработчик информации о выбранной топ-5 модели"""
        query = update.callback_query
        
        try:
            # Загружаем конфигурацию топ-5 моделей
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(__file__), 'top5_models_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                top5_models = config.get('top5_models', [])
            else:
                top5_models = []
            
            # Находим выбранную модель
            selected_model = None
            for model in top5_models:
                if model['id'] == model_id:
                    selected_model = model
                    break
            
            if not selected_model:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Модель не найдена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="top5_models_selection")
                    ]])
                )
                return
            
            # Создаем подробную информацию о модели
            text = f"🤖 <b>{selected_model['name']}</b>\n\n"
            text += f"📝 <b>Описание:</b> {selected_model['description']}\n"
            text += f"🔗 <b>ID модели:</b> <code>{selected_model['id']}</code>\n"
            text += f"📊 <b>Контекст:</b> {selected_model['context_length']:,} токенов\n"
            text += f"🏷️ <b>Категория:</b> {selected_model.get('category', 'general')}\n"
            text += f"⭐ <b>Приоритет:</b> {selected_model.get('priority', 'N/A')}\n\n"
            
            # Добавляем рекомендации
            if selected_model.get('category') == 'speed':
                text += "🚀 <b>Рекомендация:</b> Отлично подходит для быстрой суммаризации\n"
            elif selected_model.get('category') == 'quality':
                text += "🧠 <b>Рекомендация:</b> Лучшее качество для сложных задач\n"
            elif selected_model.get('category') == 'power':
                text += "💎 <b>Рекомендация:</b> Максимальная мощность для сложных чатов\n"
            elif selected_model.get('category') == 'balanced':
                text += "⚖️ <b>Рекомендация:</b> Оптимальный баланс скорости и качества\n"
            elif selected_model.get('category') == 'reliable':
                text += "🛡️ <b>Рекомендация:</b> Надежная и стабильная модель\n"
            
            text += "\n💡 <i>Эта модель будет использоваться для суммаризации ваших чатов</i>"
            
            keyboard = top5_model_info_keyboard(model_id, selected_model['name'])
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            logger.error(f"Ошибка в top5_model_info_handler: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка загрузки информации о модели: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="top5_models_selection")
                ]])
            )
    
    async def confirm_top5_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE, model_id: str):
        """Обработчик подтверждения выбора топ-5 модели"""
        query = update.callback_query
        
        try:
            # Загружаем конфигурацию топ-5 моделей
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(__file__), 'top5_models_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                top5_models = config.get('top5_models', [])
            else:
                top5_models = []
            
            # Находим выбранную модель
            selected_model = None
            for model in top5_models:
                if model['id'] == model_id:
                    selected_model = model
                    break
            
            if not selected_model:
                await TelegramMessageSender.safe_edit_message_text(
                query,
                    "❌ Модель не найдена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="top5_models_selection")
                    ]])
                )
                return
            
            # Сохраняем выбор пользователя
            user_id = query.from_user.id
            self.db.set_user_preference(user_id, 'selected_ai_provider', 'openrouter')
            self.db.set_user_preference(user_id, 'selected_openrouter_model', model_id)
            
            # Обновляем контекст для анализа
            context.user_data['selected_analysis_provider'] = 'openrouter'
            context.user_data['selected_analysis_model'] = model_id
            
            text = f"✅ <b>Модель выбрана!</b>\n\n"
            text += f"🤖 <b>{selected_model['name']}</b>\n"
            text += f"📝 {selected_model['description']}\n\n"
            text += "🎯 Теперь эта модель будет использоваться для суммаризации ваших чатов.\n\n"
            text += "💡 <i>Вы можете изменить модель в любое время через настройки AI провайдеров</i>"
            
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            if 'selected_date' in context.user_data:
                # Если мы в процессе создания новой суммаризации
                back_callback = f"select_chat_{context.user_data.get('selected_chat_id', '')}"
            else:
                # Если мы в настройках
                back_callback = "select_ai_provider"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
            ]])
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
            # Если мы в процессе создания суммаризации, запускаем анализ
            if 'selected_date' in context.user_data:
                await self._run_analysis_with_selected_model(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в confirm_top5_model_handler: {e}")
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка сохранения выбора модели: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data="top5_models_selection")
                ]])
            )
    
    async def analyze_with_openrouter_model_index_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик анализа с выбранной моделью OpenRouter по индексу"""
        query = update.callback_query
        await query.answer()
        
        try:
            index = int(query.data.split(":")[1])
            
            # Получаем полный model_id из сохраненного списка
            models_list = context.user_data.get('openrouter_models_list', [])
            if index >= len(models_list):
                raise ValueError(f"Неверный индекс модели: {index}")
            
            model_id, model_info = models_list[index]
            
            # Сохраняем выбранную модель для анализа
            context.user_data['selected_analysis_provider'] = 'openrouter'
            context.user_data['selected_analysis_model'] = model_id
            
            # Запускаем анализ с выбранной датой
            await self._run_analysis_with_selected_model(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка анализа с моделью OpenRouter по индексу: {e}")
            # Определяем правильную кнопку "Назад" в зависимости от контекста
            date = context.user_data.get('selected_date')
            if date:
                chat_id = context.user_data.get('selected_chat_id')
                back_callback = f"select_chat_{chat_id}"
            else:
                back_callback = "select_model_for_analysis"
            
            await TelegramMessageSender.safe_edit_message_text(
                query,
                f"❌ Ошибка: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=back_callback)
                ]])
            )