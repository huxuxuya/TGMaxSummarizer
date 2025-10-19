from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .service import SummaryService
from .models import Summary, SummaryType
from shared.utils import format_success_message, format_error_message, format_date_for_display
from shared.constants import CallbackActions
import logging
import time
from typing import List, Dict, Optional
from domains.ai.models import StepType

logger = logging.getLogger(__name__)

class SummaryHandlers:
    """Обработчики для работы с суммаризациями"""
    
    def __init__(self, summary_service: SummaryService, user_service=None):
        self.summary_service = summary_service
        self.user_service = user_service
    
    async def check_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик проверки суммаризации"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('check_summary_', '', 1)
            
            available_summaries = self.summary_service.get_available_summaries(vk_chat_id)
            
            if not available_summaries:
                await query.edit_message_text(
                    "📋 Нет доступных суммаризаций\n\n"
                    "Сначала выполните анализ чата."
                )
                return
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.date_selection_keyboard(available_summaries, vk_chat_id)
            
            summary_list_text = "📋 [Доступные суммаризации]:\n\n"
            for summary in available_summaries[:5]:
                date_display = format_date_for_display(summary.date)
                summary_list_text += f"📅 {date_display}\n"
            
            await query.edit_message_text(
                summary_list_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в check_summary_handler: {e}", exc_info=True)
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
            # Создаем расширенную клавиатуру с действиями
            keyboard = keyboards.summary_view_keyboard(vk_chat_id, date)
            
            # Формируем полный текст с метаданными
            metadata_text = ""
            if summary.model_provider or summary.model_id or summary.scenario_type:
                metadata_text = "\n\n📊 *Метаданные:*\n"
                if summary.model_provider:
                    metadata_text += f"   • Провайдер: {summary.model_provider}\n"
                if summary.model_id:
                    metadata_text += f"   • Модель: {summary.model_id}\n"
                if summary.scenario_type:
                    from domains.summaries.constants import SummarizationScenarios
                    scenario_name = SummarizationScenarios.get_display_name(summary.scenario_type)
                    metadata_text += f"   • Сценарий: {scenario_name}\n"
                if summary.processing_time:
                    metadata_text += f"   • Время генерации: {summary.processing_time:.2f}с\n"

            full_text = f"📋 Суммаризация за {format_date_for_display(date)}\n\n{summary.summary_text}{metadata_text}"
            
            # Разбиваем на части если нужно
            from shared.utils import format_message_for_telegram
            message_parts = format_message_for_telegram(full_text)
            
            # Логируем редактирование сообщения (если включено)
            from infrastructure.logging.message_logger import TelegramMessageLogger
            log_path = TelegramMessageLogger.log_outgoing_message(
                chat_id=query.message.chat_id,
                text=message_parts[0],
                action='edit',
                parse_mode='None',
                message_id=query.message.message_id,
                context={'handler': 'select_date_handler'}
            )

            try:
                # Отправляем первую часть с кнопками
                await query.edit_message_text(
                    message_parts[0],
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                if log_path:
                    TelegramMessageLogger.log_success(log_path, query.message.message_id)
            except Exception as e:
                if log_path:
                    TelegramMessageLogger.log_error(log_path, str(e))
                raise
            
            # Отправляем остальные части без кнопок
            for part in message_parts[1:]:
                # Логируем (если включено)
                from infrastructure.logging.message_logger import TelegramMessageLogger
                log_path = TelegramMessageLogger.log_outgoing_message(
                    chat_id=query.message.chat_id,
                    text=part,
                    action='send',
                    parse_mode='None',
                    context={
                        'handler': 'select_date_handler',
                        'part_number': message_parts.index(part) + 1
                    }
                )
                
                try:
                    message = await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        disable_web_page_preview=True
                    )
                    if log_path:
                        TelegramMessageLogger.log_success(log_path, message.message_id)
                except Exception as e:
                    if log_path:
                        TelegramMessageLogger.log_error(log_path, str(e))
            
        except Exception as e:
            logger.error(f"Ошибка в select_date_handler: {e}", exc_info=True)
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def recreate_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик пересоздания суммаризации
        
        Позволяет пользователю запустить анализ заново для существующей даты
        """
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим callback_data: recreate_summary_{vk_chat_id}_{date}
            parts = query.data.split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[2:-1])  # Поддержка vk_chat_id с подчеркиваниями
            
            # Сохраняем контекст
            context.user_data['selected_chat_id'] = vk_chat_id
            context.user_data['selected_date'] = date
            
            # Проверяем наличие сообщений за эту дату
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            messages = chat_service.get_messages_by_date(vk_chat_id, date)
            
            if not messages or len(messages) == 0:
                await query.edit_message_text(
                    f"❌ Нет сообщений за {format_date_for_display(date)} для анализа.\n\n"
                    f"Возможно, данные были удалены из базы.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"check_summary_{vk_chat_id}")
                    ]])
                )
                return
            
            # Показываем меню выбора сценария
            from infrastructure.telegram import keyboards
            
            # Получаем текущие настройки провайдера и модели
            current_provider = context.user_data.get('selected_provider', 'Не выбрано')
            current_model = context.user_data.get('selected_model_id', 'Не выбрано')
            
            # Получаем существующую суммаризацию для отображения метаинформации
            summary = self.summary_service.get_summary(vk_chat_id, date, SummaryType.DAILY)
            
            metadata_text = ""
            if summary:
                metadata_text = f"\n📊 *Текущая суммаризация:*\n"
                if summary.model_provider:
                    metadata_text += f"   • Провайдер: {summary.model_provider}\n"
                if summary.model_id:
                    metadata_text += f"   • Модель: {summary.model_id}\n"
                if summary.scenario_type:
                    from domains.summaries.constants import SummarizationScenarios
                    scenario_name = SummarizationScenarios.get_display_name(summary.scenario_type)
                    metadata_text += f"   • Сценарий: {scenario_name}\n"
            
            keyboard = keyboards.scenario_selection_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                f"🔄 *[Пересоздание суммаризации]*\n\n"
                f"📅 Дата: {format_date_for_display(date)}\n"
                f"💬 Сообщений: {len(messages)}\n"
                f"{metadata_text}\n"
                f"🤖 Текущий провайдер: {current_provider}\n"
                f"🧠 Текущая модель: {current_model}\n\n"
                f"Выберите сценарий анализа:",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в recreate_summary_handler: {e}", exc_info=True)
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации суммаризации в группу"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('publish_summary_', '', 1)
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
            keyboard = keyboards.date_selection_keyboard(available_summaries, vk_chat_id)
            
            await query.edit_message_text(
                "📤 [Публикация суммаризации]\n\n"
                "Выберите дату для публикации:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_summary_handler: {e}", exc_info=True)
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_summary_html_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик публикации суммаризации в HTML формате"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('publish_summary_html_', '', 1)
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
            keyboard = keyboards.date_selection_keyboard(available_summaries, vk_chat_id)
            
            await query.edit_message_text(
                "📤 [Публикация суммаризации] (HTML)\n\n"
                "Выберите дату для публикации:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_summary_html_handler: {e}", exc_info=True)
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
            
            logger.info(f"🔍 publish_to_group_handler: date={date}, vk_chat_id={vk_chat_id}, group_id={group_id}, use_html={use_html}")
            
            if not all([date, vk_chat_id, group_id]):
                logger.warning(f"❌ Не все параметры выбраны: date={date}, vk_chat_id={vk_chat_id}, group_id={group_id}")
                await query.edit_message_text(
                    "❌ Не все параметры выбраны"
                )
                return
            
            summary = self.summary_service.get_summary(vk_chat_id, date, SummaryType.DAILY)
            logger.info(f"🔍 publish_to_group_handler: summary found = {summary is not None}")
            
            if not summary:
                logger.info(f"🔍 publish_to_group_handler: суммаризация не найдена, проверяем сообщения")
                # Проверяем, есть ли сообщения за эту дату
                from domains.chats.repository import MessageRepository
                from core.database.connection import DatabaseConnection
                
                db_connection = DatabaseConnection('bot_database.db')
                message_repo = MessageRepository(db_connection)
                messages_count = message_repo.get_messages_count_for_date(vk_chat_id, date)
                
                logger.info(f"🔍 publish_to_group_handler: messages_count = {messages_count}")
                
                if messages_count > 0:
                    # Есть сообщения, но нет суммаризации - предлагаем создать
                    from infrastructure.telegram import keyboards
                    keyboard = keyboards.scenario_selection_keyboard(vk_chat_id, date)
                    
                    logger.info(f"🔍 publish_to_group_handler: отправляем сообщение с предложением создать суммаризацию")
                    await query.edit_message_text(
                        f"❌ Суммаризация за {format_date_for_display(date)} не найдена\n\n"
                        f"📊 Найдено {messages_count} сообщений за эту дату\n\n"
                        f"💡 Сначала создайте суммаризацию:",
                        reply_markup=keyboard
                    )
                else:
                    # Нет ни сообщений, ни суммаризации
                    logger.info(f"🔍 publish_to_group_handler: нет сообщений за эту дату")
                    await query.edit_message_text(
                        f"❌ Суммаризация за {format_date_for_display(date)} не найдена\n\n"
                        f"📊 Нет сообщений за эту дату"
                    )
                return
            
            from infrastructure.telegram import sender
            from infrastructure.telegram import formatter
            from infrastructure.telegram.sender import ParseMode
            from shared.utils import format_summary_for_telegram_html_universal
            
            # Определяем, какой текст публиковать
            if summary.reflection_text or summary.improved_summary_text:
                # Публикуем улучшенную версию или все компоненты
                text_to_publish = summary.improved_summary_text or summary.summary_text
            else:
                # Публикуем обычную суммаризацию
                text_to_publish = summary.summary_text
            
            if use_html:
                formatted_parts = format_summary_for_telegram_html_universal(
                    text_to_publish, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = ParseMode.HTML
            else:
                from shared.utils import format_summary_for_telegram
                formatted_parts = format_summary_for_telegram(
                    text_to_publish, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = ParseMode.MARKDOWN_V2
            
            for part in formatted_parts:
                if use_html:
                    # Для HTML используем прямой вызов bot.send_message
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=part,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                else:
                    # Для Markdown используем safe_send_message
                    await sender.TelegramMessageSender.safe_send_message(
                        context.bot,
                        group_id,
                        part,
                        parse_mode=parse_mode
                    )
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                format_success_message(
                    f"Суммаризация опубликована в группу"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в publish_to_group_handler: {e}", exc_info=True)
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def create_for_date_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создать суммаризацию для выбранной даты"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг
            # create_for_date_{vk_chat_id}_{date}
            data_without_prefix = query.data.replace('create_for_date_', '', 1)
            # Разделяем справа, чтобы получить последнюю часть как date
            parts = data_without_prefix.rsplit('_', 1)
            
            if len(parts) != 2:
                raise ValueError(f"Неверный формат callback_data: {query.data}")
                
            vk_chat_id = parts[0]
            date = parts[1]
            
            context.user_data['selected_chat_id'] = vk_chat_id
            context.user_data['selected_date'] = date
            
            # Показываем выбор сценария
            from infrastructure.telegram import keyboards
            keyboard = keyboards.scenario_selection_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                f"📋 Выберите сценарий суммаризации для {date}\n\n"
                f"⚡ **Быстрая** - только суммаризация (1-2 мин)\n"
                f"🔄 **С рефлексией** - анализ и улучшение (2-4 мин)\n"
                f"🧹 **С очисткой** - фильтрация + суммаризация (3-5 мин)\n"
                f"🔍 **Структурированная** - детальный анализ (4-6 мин)",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в create_for_date_handler: {e}", exc_info=True)
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def publish_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню публикации с выбором даты"""
        query = update.callback_query
        await query.answer()
        
        try:
            # ИСПРАВЛЕНО: правильный парсинг vk_chat_id с подчеркиваниями
            vk_chat_id = query.data.replace('publish_menu_', '', 1)
            
            # Получаем доступные суммаризации
            summaries = self.summary_service.get_available_summaries(vk_chat_id)
            
            if not summaries:
                await query.edit_message_text(
                    "❌ Нет доступных суммаризаций для публикации\n\n"
                    "Сначала создайте суммаризацию."
                )
                return
            
            # Показываем список дат с суммаризациями
            keyboard = []
            for summary in summaries[:10]:
                date_str = summary.date
                # Handle both enum and string types for summary_type
                summary_type_display = summary.summary_type.value if hasattr(summary.summary_type, 'value') else str(summary.summary_type)
                keyboard.append([InlineKeyboardButton(
                    f"📅 {date_str} ({summary_type_display})",
                    callback_data=f"select_publish_date_{vk_chat_id}_{date_str}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"quick_chat_{vk_chat_id}")])
            
            await query.edit_message_text(
                "📤 [Публикация суммаризации]\n\n"
                "Выберите дату суммаризации для публикации:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Ошибка в publish_menu_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def select_publish_date_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выбрать дату суммаризации и показать форматы"""
        query = update.callback_query
        await query.answer()
        
        try:
            # select_publish_date_{vk_chat_id}_{date}
            parts = query.data.split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[3:-1])
            
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.publish_format_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                f"📤 [Публикация суммаризации] за {date}\n\n"
                "Выберите формат:",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Ошибка в select_publish_date_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def select_scenario_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора сценария"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: scenario_{type}_{vk_chat_id}_{date}
            parts = query.data.replace('scenario_', '', 1).split('_')
            scenario_type = parts[0]
            date = parts[-1]
            vk_chat_id = '_'.join(parts[1:-1])
            
            # Сохраняем выбранный сценарий
            context.user_data['selected_scenario'] = scenario_type
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            
            # Save scenario selection to database
            if self.user_service:
                self.user_service.save_user_ai_settings(
                    update.effective_user.id, 
                    scenario=scenario_type
                )
            
            # Проверяем, есть ли уже выбранная модель
            current_provider = context.user_data.get('confirmed_provider')
            current_model = context.user_data.get('selected_model_id')
            
            if current_provider and current_model and current_provider != 'Не выбрано' and current_model != 'Не выбрано':
                # Модель уже выбрана - запускаем анализ сразу
                print(f"🔍 DEBUG: Модель уже выбрана, запускаем анализ сразу:")
                print(f"   provider: {current_provider}")
                print(f"   model: {current_model}")
                print(f"   scenario: {scenario_type}")
                
                # Показываем сообщение о запуске анализа
                from domains.summaries.constants import SummarizationScenarios
                scenario_names = SummarizationScenarios.NAMES
                
                await query.edit_message_text(
                    f"🚀 Запускаем анализ...\n\n"
                    f"📋 Сценарий: {scenario_names.get(scenario_type, scenario_type)}\n"
                    f"🤖 Провайдер: {current_provider}\n"
                    f"🧠 Модель: {current_model}\n"
                    f"📅 Дата: {date}\n\n"
                    f"Это может занять несколько минут."
                )
                
                # Запускаем анализ напрямую
                await self._run_actual_analysis(query, vk_chat_id, date, scenario_type, current_provider, current_model, context)
            else:
                # Модель не выбрана - показываем выбор модели
                print(f"🔍 DEBUG: Модель не выбрана, показываем выбор модели:")
                print(f"   provider: {current_provider}")
                print(f"   model: {current_model}")
                
                await self._show_model_selection_for_scenario(update, context)
            
        except Exception as e:
            logger.error(f"Ошибка в select_scenario_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))

    async def _show_model_selection_for_scenario(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выбор модели для выбранного сценария"""
        query = update.callback_query
        
        try:
            scenario = context.user_data.get('selected_scenario')
            date = context.user_data.get('selected_date')
            vk_chat_id = context.user_data.get('selected_chat_id')
            
            # Маппинг названий сценариев
            scenario_names = {
                'fast': '⚡ Быстрая',
                'reflection': '🔄 С рефлексией',
                'cleaning': '🧹 С очисткой',
                'structured': '🔍 Структурированная'
            }
            
            # Получаем текущую выбранную модель (используем те же ключи, что и в AI handlers)
            current_provider = context.user_data.get('confirmed_provider', 'Не выбрано')
            current_model = context.user_data.get('selected_model_id', 'Не выбрано')
            current_default_scenario = context.user_data.get('default_scenario', 'fast')
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.model_selection_for_summary_keyboard(vk_chat_id, date, scenario)
            
            await query.edit_message_text(
                f"🤖 [Выбор модели] для суммаризации\n\n"
                f"📋 Сценарий: {scenario_names.get(scenario, scenario)}\n"
                f"📅 Дата: {date}\n\n"
                f"🤖 Провайдер: {current_provider}\n"
                f"🧠 Модель: {current_model}\n"
                f"⚙️ Дефолтный сценарий: {scenario_names.get(current_default_scenario, current_default_scenario)}\n\n"
                f"Хотите изменить модель или запустить с текущей?",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _show_model_selection_for_scenario: {e}")
            await query.edit_message_text(format_error_message(e))
    
    async def run_summary_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик запуска суммаризации с выбранными параметрами"""
        query = update.callback_query
        await query.answer()
        
        print(f"🔍 DEBUG: run_summary_handler вызван с callback_data: {query.data}")
        logger.info(f"🔍 DEBUG: run_summary_handler вызван с callback_data: {query.data}")
        
        try:
            # Парсим: run_summary_{vk_chat_id}_{date}_{scenario}
            parts = query.data.replace('run_summary_', '', 1).split('_')
            scenario = parts[-1]
            date = parts[-2]
            vk_chat_id = '_'.join(parts[:-2])
            
            # Получаем параметры (используем те же ключи, что и в AI handlers)
            provider = context.user_data.get('confirmed_provider', 'Не выбрано')
            model = context.user_data.get('selected_model_id', 'Не выбрано')
            
            # Маппинг названий сценариев
            scenario_names = {
                'fast': '⚡ Быстрая',
                'reflection': '🔄 С рефлексией',
                'cleaning': '🧹 С очисткой',
                'structured': '🔍 Структурированная'
            }
            
            await query.edit_message_text(
                f"🚀 Запускаем анализ...\n\n"
                f"📋 Сценарий: {scenario_names.get(scenario, scenario)}\n"
                f"🤖 Провайдер: {provider}\n"
                f"🧠 Модель: {model}\n"
                f"📅 Дата: {date}\n\n"
                f"Это может занять несколько минут."
            )
            
            # Выполняем реальный анализ
            await self._run_actual_analysis(query, vk_chat_id, date, scenario, provider, model, context)
            
        except Exception as e:
            logger.error(f"Ошибка в run_summary_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    def _convert_scenario_to_steps(self, scenario: str, clean_data_first: bool) -> List[StepType]:
        """Конвертирует старый формат сценария в новый список шагов"""
        from domains.ai.models import StepType
        
        steps = []
        
        # Добавляем очистку данных если нужно
        if clean_data_first:
            steps.append(StepType.CLEANING)
        
        # Основные шаги в зависимости от сценария
        if scenario == 'fast':
            steps.append(StepType.SUMMARIZATION)
        elif scenario == 'reflection':
            steps.extend([StepType.SUMMARIZATION, StepType.REFLECTION, StepType.IMPROVEMENT])
        elif scenario == 'cleaning':
            steps.extend([StepType.CLEANING, StepType.SUMMARIZATION])
        elif scenario == 'structured':
            steps.extend([StepType.SUMMARIZATION, StepType.CLASSIFICATION, StepType.EXTRACTION, StepType.PARENT_SUMMARY])
        elif scenario == 'with_schedule':
            steps.extend([StepType.SUMMARIZATION, StepType.SCHEDULE_ANALYSIS])
        elif scenario == 'full':
            steps.extend([StepType.CLEANING, StepType.SUMMARIZATION, StepType.REFLECTION, StepType.IMPROVEMENT, StepType.CLASSIFICATION, StepType.EXTRACTION, StepType.SCHEDULE_ANALYSIS, StepType.PARENT_SUMMARY])
        else:
            # По умолчанию - только суммаризация
            steps.append(StepType.SUMMARIZATION)
        
        return steps

    def _map_scenario_to_analysis_type(self, scenario: str) -> tuple:
        """
        Преобразовать сценарий в параметры AnalysisRequest
        
        Returns:
            tuple: (analysis_type, clean_data_first)
        """
        from domains.ai.models import AnalysisType
        
        if scenario == 'fast':
            return (AnalysisType.SUMMARIZATION, False)
        elif scenario == 'reflection':
            return (AnalysisType.REFLECTION, False)
        elif scenario == 'structured':
            return (AnalysisType.STRUCTURED, False)
        elif scenario == 'cleaning':
            return (AnalysisType.SUMMARIZATION, True)
        else:
            # По умолчанию - быстрая суммаризация
            return (AnalysisType.SUMMARIZATION, False)

    async def _run_actual_analysis(self, query, vk_chat_id: str, date: str, scenario: str, provider: str, model: str, context: ContextTypes.DEFAULT_TYPE):
        """Выполнить реальный анализ чата"""
        print(f"🔍 DEBUG: _run_actual_analysis вызван с параметрами:")
        print(f"   vk_chat_id: {vk_chat_id}")
        print(f"   date: {date}")
        print(f"   scenario: {scenario}")
        print(f"   provider: {provider}")
        print(f"   model: {model}")
        logger.info(f"🔍 DEBUG: _run_actual_analysis вызван с параметрами:")
        logger.info(f"   vk_chat_id: {vk_chat_id}")
        logger.info(f"   date: {date}")
        logger.info(f"   scenario: {scenario}")
        logger.info(f"   provider: {provider}")
        logger.info(f"   model: {model}")
        
        # Определяем тип анализа на основе сценария
        analysis_type, clean_data_first = self._map_scenario_to_analysis_type(scenario)
        logger.info(f"📋 Выбранный сценарий: {scenario}")
        logger.info(f"📋 Тип анализа: {analysis_type}")
        logger.info(f"📋 Предварительная очистка: {clean_data_first}")
        
        try:
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            from domains.ai.models import AnalysisRequest, AnalysisType
            from domains.summaries.models import Summary, SummaryType
            from shared.utils import format_success_message, format_error_message
            
            # Получаем сообщения для анализа
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            messages = chat_service.get_messages_by_date(vk_chat_id, date)
            
            if not messages:
                await query.edit_message_text(
                    "❌ Нет сообщений для анализа за указанную дату"
                )
                return
            
            # Конвертируем сообщения в нужный формат
            messages_data = [msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict() for msg in messages]
            
            # Отладочная информация
            print(f"🔍 DEBUG: Создаем AnalysisRequest с параметрами:")
            print(f"   provider_name: {provider}")
            print(f"   model_id: {model}")
            print(f"   user_id: {query.from_user.id}")
            logger.info(f"🔍 DEBUG: Создаем AnalysisRequest с параметрами:")
            logger.info(f"   provider_name: {provider}")
            logger.info(f"   model_id: {model}")
            logger.info(f"   user_id: {query.from_user.id}")
            
            # Создаем запрос на анализ
            # Получаем AI сервис из контекста
            from core.app_context import get_app_context
            ctx = get_app_context()
            ai_service = ctx.ai_service
            
            # Создаем LLM Logger для логирования запросов/ответов
            llm_logger = self._create_llm_logger(date, scenario, model, provider, query.from_user.id)
            
            # Конвертируем старый формат в новый
            from domains.ai.models import StepType
            steps = self._convert_scenario_to_steps(scenario, clean_data_first)
            
            analysis_request = AnalysisRequest(
                messages=messages_data,
                provider_name=provider,
                model_id=model,
                user_id=query.from_user.id,
                chat_context={'group_id': 1, 'date': date},  # TODO: получить реальный group_id
                llm_logger=llm_logger,
                steps=steps  # ✅ ИСПОЛЬЗУЕМ НОВУЮ АРХИТЕКТУРУ
            )
            
            # Выполняем анализ
            result = await ai_service.analyze_chat(analysis_request)
            
            if result.success:
                # Извлекаем структурированные данные
                step_data = self.summary_service.extract_step_results_from_analysis(
                    result, scenario
                )

                # Создаем объект Summary с заполненными полями
                summary = Summary(
                    vk_chat_id=vk_chat_id,
                    date=date,
                    summary_text=step_data.get('summary') or result.result,
                    reflection_text=step_data.get('reflection'),
                    improved_summary_text=step_data.get('improved'),
                    classification_data=step_data.get('classification'),
                    extraction_data=step_data.get('extraction'),
                    parent_summary_text=step_data.get('parent_summary'),
                    provider_name=result.provider_name,
                    processing_time=result.processing_time,
                    model_provider=provider,
                    model_id=model,
                    scenario_type=scenario,
                    generation_time_seconds=result.processing_time
                )

                self.summary_service.save_summary(summary)
                
                # Маппинг названий сценариев
                scenario_names = {
                    'fast': '⚡ Быстрая',
                    'reflection': '🔄 С рефлексией',
                    'cleaning': '🧹 С очисткой',
                    'structured': '🔍 Структурированная'
                }
                
                from infrastructure.telegram import keyboards
                keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
                
                # Определяем, что показывать пользователю
                display_text = self._get_display_text_for_scenario(
                    scenario, step_data, result.result
                )
                
                # Формируем чистый результат без метаданных
                result_text = display_text
                
                # Разбиваем на части если нужно
                from shared.utils import format_message_for_telegram
                message_parts = format_message_for_telegram(result_text)
                
                # Логируем редактирование сообщения (если включено)
                from infrastructure.logging.message_logger import TelegramMessageLogger
                log_path = TelegramMessageLogger.log_outgoing_message(
                    chat_id=query.message.chat_id,
                    text=message_parts[0],
                    action='edit',
                    parse_mode='Markdown',
                    message_id=query.message.message_id,
                    context={
                        'handler': '_run_actual_analysis',
                        'scenario': scenario,
                        'provider': provider,
                        'model': model,
                        'is_result': True
                    }
                )

                try:
                    # Отправляем первую часть с кнопками, без обертки format_success_message
                    await query.edit_message_text(
                        message_parts[0],
                        reply_markup=keyboard,
                        disable_web_page_preview=True,
                        parse_mode='Markdown'
                    )
                    
                    # Обновляем лог при успехе
                    if log_path:
                        TelegramMessageLogger.log_success(log_path, query.message.message_id)
                        
                except Exception as e:
                    # Обновляем лог при ошибке
                    if log_path:
                        TelegramMessageLogger.log_error(log_path, str(e))
                    raise
                
                # Отправляем остальные части без кнопок
                for part in message_parts[1:]:
                    # Логируем (если включено)
                    from infrastructure.logging.message_logger import TelegramMessageLogger
                    log_path = TelegramMessageLogger.log_outgoing_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        action='send',
                        parse_mode='Markdown',
                        context={
                            'handler': '_run_actual_analysis',
                            'scenario': scenario,
                            'part_number': message_parts.index(part) + 1
                        }
                    )
                    
                    try:
                        message = await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=part,
                            disable_web_page_preview=True,
                            parse_mode='Markdown'
                        )
                        if log_path:
                            TelegramMessageLogger.log_success(log_path, message.message_id)
                    except Exception as e:
                        if log_path:
                            TelegramMessageLogger.log_error(log_path, str(e))
            else:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
                
                await query.edit_message_text(
                    f"❌ Ошибка анализа: {result.error}",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в _run_actual_analysis: {e}")
            from infrastructure.telegram import keyboards
            keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    def _get_display_text_for_scenario(
        self, 
        scenario: str, 
        step_data: Dict[str, Optional[str]], 
        fallback_result: str
    ) -> str:
        """
        Выбрать правильный текст для отображения в зависимости от сценария
        
        Args:
            scenario: Тип сценария (fast, reflection, cleaning, structured)
            step_data: Извлеченные структурированные данные
            fallback_result: Резервный текст если нет структурированных данных
            
        Returns:
            Текст для отображения пользователю
        """
        if scenario == 'reflection':
            # Для рефлексии показываем только улучшенную версию
            if step_data.get('improved'):
                return step_data['improved']
            # Если нет улучшенной, показываем исходную суммаризацию
            elif step_data.get('summary'):
                return step_data['summary']
        
        elif scenario == 'structured':
            # Для структурированного анализа показываем сводку для родителей
            if step_data.get('parent_summary'):
                return step_data['parent_summary']
            # Или исходную суммаризацию
            elif step_data.get('summary'):
                return step_data['summary']
        
        elif scenario in ['fast', 'cleaning']:
            # Для быстрой/очищенной показываем суммаризацию
            if step_data.get('summary'):
                return step_data['summary']
        
        # Fallback на полный результат
        return fallback_result
    
    async def preset_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора пресета"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: preset_{type}_{vk_chat_id}_{date}
            parts = query.data.replace('preset_', '', 1).split('_')
            preset_type = parts[0]
            date = parts[-1]
            vk_chat_id = '_'.join(parts[1:-1])
            
            await self._handle_preset_selection(update, context, preset_type, vk_chat_id, date)
            
        except Exception as e:
            logger.error(f"Ошибка в preset_selection_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def _handle_preset_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, preset_type: str, vk_chat_id: str, date: str):
        """Обработка выбора пресета"""
        query = update.callback_query
        
        # Получаем пресет
        from domains.ai.presets import PresetRegistry
        preset = PresetRegistry.get_preset(preset_type)
        
        if not preset:
            # Fallback для legacy сценариев
            legacy_mapping = {
                'fast': 'fast',
                'reflection': 'reflection', 
                'cleaning': 'cleaning',
                'structured': 'structured'
            }
            preset_type = legacy_mapping.get(preset_type, 'fast')
            preset = PresetRegistry.get_preset(preset_type)
        
        # Сохраняем выбранные шаги
        context.user_data['selected_steps'] = [step.value for step in preset.steps]
        context.user_data['selected_scenario'] = preset_type  # Для совместимости
        context.user_data['selected_date'] = date
        context.user_data['selected_chat_id'] = vk_chat_id
        
        # Save scenario selection to database
        if self.user_service:
            self.user_service.save_user_ai_settings(
                update.effective_user.id, 
                scenario=preset_type
            )
        
        # Проверяем, есть ли уже выбранная модель
        current_provider = context.user_data.get('confirmed_provider')
        current_model = context.user_data.get('selected_model_id')
        
        if current_provider and current_model and current_provider != 'Не выбрано' and current_model != 'Не выбрано':
            # Модель уже выбрана - запускаем анализ сразу
            await query.edit_message_text(
                f"🚀 Запускаем анализ...\n\n"
                f"📋 Пресет: {preset.icon} {preset.name}\n"
                f"🤖 Провайдер: {current_provider}\n"
                f"🧠 Модель: {current_model}\n"
                f"📅 Дата: {date}\n"
                f"🔧 Шаги: {', '.join([step.value for step in preset.steps])}\n\n"
                f"Это может занять несколько минут."
            )
            
            # Запускаем анализ с новыми шагами
            await self._run_analysis_with_steps(query, vk_chat_id, date, preset.steps, current_provider, current_model, context)
        else:
            # Модель не выбрана - показываем выбор модели
            await self._show_model_selection_for_preset(update, context, preset)
    
    async def custom_pipeline_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик конструктора пользовательского pipeline"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: custom_pipeline_{vk_chat_id}_{date}
            parts = query.data.replace('custom_pipeline_', '', 1).split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[:-1])
            
            # Загружаем сохраненную конфигурацию или используем текущую
            from domains.ai.models import StepType
            if 'custom_steps' not in context.user_data:
                # Загружаем из БД
                context.user_data['custom_steps'] = await self._load_custom_steps(update.effective_user.id)
            
            selected_steps = context.user_data.get('custom_steps', [StepType.SUMMARIZATION])
            
            # Сохраняем контекст
            context.user_data['selected_date'] = date
            context.user_data['selected_chat_id'] = vk_chat_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.custom_pipeline_keyboard(vk_chat_id, date, selected_steps)
            
            await query.edit_message_text(
                "🎨 [Конструктор анализа]\n\n"
                "Выберите шаги для выполнения:\n"
                "(Нажмите на шаг чтобы включить/выключить)\n\n"
                "💡 Ваша последняя конфигурация загружена автоматически",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в custom_pipeline_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def toggle_step_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle шага в конструкторе"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: toggle_step_{step_name}_{vk_chat_id}_{date}
            parts = query.data.replace('toggle_step_', '', 1).split('_')
            step_name = parts[0]
            date = parts[-1]
            vk_chat_id = '_'.join(parts[1:-1])
            
            from domains.ai.models import StepType
            step_type = StepType(step_name)
            
            custom_steps = context.user_data.get('custom_steps', [StepType.SUMMARIZATION])
            
            if step_type in custom_steps:
                custom_steps.remove(step_type)
            else:
                custom_steps.append(step_type)
            
            context.user_data['custom_steps'] = custom_steps
            
            # Перерисовываем меню
            from infrastructure.telegram import keyboards
            keyboard = keyboards.custom_pipeline_keyboard(vk_chat_id, date, custom_steps)
            
            await query.edit_message_text(
                "🎨 [Конструктор анализа]\n\n"
                "Выберите шаги для выполнения:\n"
                "(Нажмите на шаг чтобы включить/выключить)",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в toggle_step_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def _run_analysis_with_steps(self, query, vk_chat_id: str, date: str, steps, provider: str, model: str, context: ContextTypes.DEFAULT_TYPE):
        """Запуск анализа с новыми шагами"""
        try:
            # Получаем сообщения
            from core.app_context import get_app_context
            ctx = get_app_context()
            messages = ctx.chat_service.get_messages_by_date(vk_chat_id, date)
            if not messages:
                await query.edit_message_text("❌ Нет сообщений для анализа")
                return
            
            # Конвертируем сообщения в словари
            messages_data = [msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict() for msg in messages]
            
            # Определить scenario на основе выбранных шагов
            scenario = self._get_scenario_name_from_steps(steps)
            
            # Создать llm_logger с правильными параметрами
            llm_logger = self._create_llm_logger(date, scenario, model, provider, context.user_data.get('user_id'))
            
            # Создаем запрос с новыми шагами
            from domains.ai.models import AnalysisRequest, StepType
            request = AnalysisRequest(
                messages=messages_data,
                provider_name=provider,
                model_id=model,
                user_id=context.user_data.get('user_id'),
                chat_context={'group_id': 1, 'date': date},  # TODO: получить реальный group_id
                llm_logger=llm_logger,  # Используем созданный logger
                steps=steps
            )
            
            # Запускаем анализ
            result = await ctx.ai_service.analyze_chat(request)
            
            if result.success:
                # Показываем результат
                from infrastructure.telegram import keyboards
                keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
                
                # Извлекаем структурированные данные из результата
                step_data = self.summary_service.extract_step_results_from_analysis(
                    result, scenario
                )
                
                # Определяем, что показывать пользователю (только финальный результат)
                display_text = self._get_display_text_for_scenario(
                    scenario, step_data, result.result
                )
                
                # Создаем объект Summary с заполненными полями
                summary = Summary(
                    vk_chat_id=vk_chat_id,
                    date=date,
                    summary_text=step_data.get('summary') or result.result,
                    reflection_text=step_data.get('reflection'),
                    improved_summary_text=step_data.get('improved'),
                    classification_data=step_data.get('classification'),
                    extraction_data=step_data.get('extraction'),
                    parent_summary_text=step_data.get('parent_summary'),
                    provider_name=result.provider_name,
                    processing_time=result.processing_time,
                    model_provider=provider,
                    model_id=model,
                    scenario_type=scenario,
                    generation_time_seconds=result.processing_time
                )

                # Сохраняем суммаризацию в БД
                self.summary_service.save_summary(summary)
                logger.info(f"✅ Суммаризация сохранена в БД: {vk_chat_id}, {date}")
                
                result_text = f"✅ Анализ завершен за {result.processing_time:.2f}с\n\n"
                result_text += f"🔧 Выполненные шаги: {', '.join(result.metadata.get('executed_steps', []))}\n"
                result_text += f"🤖 Провайдер: {result.provider_name}\n"
                result_text += f"🧠 Модель: {model}\n"
                result_text += f"📅 Дата: {date}\n\n"
                result_text += f"📝 Результат:\n{display_text}"
                
                # Разбиваем на части если нужно
                from shared.utils import format_message_for_telegram
                message_parts = format_message_for_telegram(result_text)
                
                # Логируем редактирование сообщения (если включено)
                from infrastructure.logging.message_logger import TelegramMessageLogger
                log_path = TelegramMessageLogger.log_outgoing_message(
                    chat_id=query.message.chat_id,
                    text=format_success_message(message_parts[0]),
                    action='edit',
                    parse_mode='None',
                    message_id=query.message.message_id,
                    context={'handler': 'preset_selection_handler'}
                )

                try:
                    # Отправляем первую часть с кнопками
                    await query.edit_message_text(
                        format_success_message(message_parts[0]),
                        reply_markup=keyboard,
                        disable_web_page_preview=True
                    )
                    if log_path:
                        TelegramMessageLogger.log_success(log_path, query.message.message_id)
                except Exception as e:
                    if log_path:
                        TelegramMessageLogger.log_error(log_path, str(e))
                    raise
                
                # Отправляем остальные части без кнопок
                for part in message_parts[1:]:
                    # Логируем (если включено)
                    from infrastructure.logging.message_logger import TelegramMessageLogger
                    log_path = TelegramMessageLogger.log_outgoing_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        action='send',
                        parse_mode='None',
                        context={
                            'handler': 'preset_selection_handler',
                            'scenario': scenario,
                            'part_number': message_parts.index(part) + 1
                        }
                    )
                    
                    try:
                        message = await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=format_success_message(part),
                            disable_web_page_preview=True
                        )
                        if log_path:
                            TelegramMessageLogger.log_success(log_path, message.message_id)
                    except Exception as e:
                        if log_path:
                            TelegramMessageLogger.log_error(log_path, str(e))
            else:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
                
                await query.edit_message_text(
                    f"❌ Ошибка анализа: {result.error}",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в _run_analysis_with_steps: {e}")
            from infrastructure.telegram import keyboards
            keyboard = keyboards.summary_result_keyboard(vk_chat_id, date)
            
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def run_custom_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик запуска кастомного анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: run_custom_{vk_chat_id}_{date}
            parts = query.data.replace('run_custom_', '', 1).split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[:-1])
            
            # Получаем выбранные шаги
            from domains.ai.models import StepType
            custom_steps = context.user_data.get('custom_steps', [StepType.SUMMARIZATION])
            
            # Валидация
            if not custom_steps:
                await query.edit_message_text("❌ Не выбрано ни одного шага")
                return
            
            # Сохраняем конфигурацию
            await self._save_custom_steps(update.effective_user.id, custom_steps)
            
            # Проверяем модель
            current_provider = context.user_data.get('confirmed_provider')
            current_model = context.user_data.get('selected_model_id')
            
            if current_provider and current_model and current_provider != 'Не выбрано' and current_model != 'Не выбрано':
                # Запускаем анализ
                steps_display = ', '.join([s.value for s in custom_steps])
                await query.edit_message_text(
                    f"🚀 Запускаем кастомный анализ...\n\n"
                    f"🔧 Шаги: {steps_display}\n"
                    f"🤖 Провайдер: {current_provider}\n"
                    f"🧠 Модель: {current_model}\n"
                    f"📅 Дата: {date}\n\n"
                    f"💾 Конфигурация сохранена автоматически\n\n"
                    f"Это может занять несколько минут."
                )
                
                await self._run_analysis_with_steps(query, vk_chat_id, date, custom_steps, current_provider, current_model, context)
            else:
                # Показываем выбор модели
                await query.edit_message_text(
                    "⚠️ Сначала выберите AI провайдера и модель в настройках\n\n"
                    "💾 Ваша конфигурация сохранена",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⚙️ Настройки AI", callback_data="select_ai_provider"),
                        InlineKeyboardButton("🔙 Назад", callback_data=f"custom_pipeline_{vk_chat_id}_{date}")
                    ]])
                )
        
        except Exception as e:
            logger.error(f"Ошибка в run_custom_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def _save_custom_steps(self, user_id: int, steps: list):
        """Сохранить конфигурацию конструктора"""
        import json
        
        if self.user_service:
            try:
                steps_json = json.dumps([s.value if hasattr(s, 'value') else s for s in steps])
                self.user_service.save_user_ai_settings(user_id, custom_steps=steps_json)
                logger.info(f"💾 Сохранена конфигурация конструктора для пользователя {user_id}: {steps_json}")
            except Exception as e:
                logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    async def _load_custom_steps(self, user_id: int) -> list:
        """Загрузить сохраненную конфигурацию конструктора"""
        import json
        
        if self.user_service:
            try:
                settings = self.user_service.get_user_ai_settings(user_id)
                if settings and 'custom_steps' in settings:
                    from domains.ai.models import StepType
                    steps_list = json.loads(settings['custom_steps'])
                    steps = [StepType(s) for s in steps_list]
                    logger.info(f"📂 Загружена конфигурация конструктора для пользователя {user_id}: {steps}")
                    return steps
            except Exception as e:
                logger.error(f"Ошибка загрузки конфигурации: {e}")
        
        # По умолчанию только суммаризация
        from domains.ai.models import StepType
        return [StepType.SUMMARIZATION]
    
    def _create_llm_logger(self, date: str, scenario: str, model: str, provider: str, user_id: int):
        """Создать LLM Logger с правильными параметрами"""
        from infrastructure.logging.llm_logger import LLMLogger
        import os
        
        LLM_LOGS_DIR = os.environ.get('LLM_LOGS_DIR', 'llm_logs')
        
        llm_logger = LLMLogger(
            LLM_LOGS_DIR,
            date=date,
            scenario=scenario,
            test_mode=False,
            model_name=model
        )
        llm_logger.set_session_info(provider, model, None, user_id)
        
        logger.info(f"📁 LLM Logger создан: {llm_logger.get_logs_path()}")
        
        return llm_logger
    
    def _get_scenario_name_from_steps(self, steps):
        """Получить имя сценария на основе шагов"""
        from domains.ai.models import StepType
        
        if len(steps) == 1 and steps[0] == StepType.SUMMARIZATION:
            return "fast"
        elif set(steps) == {StepType.SUMMARIZATION, StepType.REFLECTION, StepType.IMPROVEMENT}:
            return "reflection"
        elif StepType.CLEANING in steps and StepType.SUMMARIZATION in steps:
            return "cleaning"
        elif any(s in steps for s in [StepType.CLASSIFICATION, StepType.EXTRACTION]):
            return "structured"
        else:
            # Генерируем имя из списка шагов
            return "custom_" + "_".join([s.value for s in steps])
    
    async def save_custom_preset_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сохранения пользовательского пресета"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим: save_custom_preset_{vk_chat_id}_{date}
            parts = query.data.replace('save_custom_preset_', '', 1).split('_')
            date = parts[-1]
            vk_chat_id = '_'.join(parts[:-1])
            
            # Получаем выбранные шаги
            from domains.ai.models import StepType
            custom_steps = context.user_data.get('custom_steps', [StepType.SUMMARIZATION])
            
            if not custom_steps:
                await query.edit_message_text("❌ Не выбрано ни одного шага для сохранения")
                return
            
            # Показываем форму для ввода названия пресета
            await query.edit_message_text(
                "💾 [Сохранение пресета]\n\n"
                f"Выбранные шаги: {', '.join([s.value for s in custom_steps])}\n\n"
                "Введите название для вашего пресета:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Назад", callback_data=f"custom_pipeline_{vk_chat_id}_{date}")
                ]])
            )
            
            # Устанавливаем состояние ожидания названия
            context.user_data['waiting_for_preset_name'] = True
            context.user_data['preset_steps'] = custom_steps
            context.user_data['preset_vk_chat_id'] = vk_chat_id
            context.user_data['preset_date'] = date
            
        except Exception as e:
            logger.error(f"Ошибка в save_custom_preset_handler: {e}", exc_info=True)
            await query.edit_message_text(format_error_message(e))
    
    async def handle_preset_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода названия пресета"""
        if not context.user_data.get('waiting_for_preset_name'):
            return
        
        try:
            preset_name = update.message.text.strip()
            if not preset_name:
                await update.message.reply_text("❌ Название не может быть пустым")
                return
            
            # Получаем данные из context
            steps = context.user_data.get('preset_steps', [])
            vk_chat_id = context.user_data.get('preset_vk_chat_id')
            date = context.user_data.get('preset_date')
            
            # Сохраняем пресет (пока в context, позже можно в БД)
            user_id = update.effective_user.id
            if 'user_presets' not in context.user_data:
                context.user_data['user_presets'] = {}
            
            # Создаем уникальный ID для пресета
            preset_id = f"user_{user_id}_{int(time.time())}"
            
            context.user_data['user_presets'][preset_id] = {
                'name': preset_name,
                'steps': [s.value for s in steps],
                'created_at': time.time()
            }
            
            # Очищаем состояние
            context.user_data.pop('waiting_for_preset_name', None)
            context.user_data.pop('preset_steps', None)
            context.user_data.pop('preset_vk_chat_id', None)
            context.user_data.pop('preset_date', None)
            
            # Показываем успех
            await update.message.reply_text(
                f"✅ Пресет \"{preset_name}\" сохранен!\n\n"
                f"Шаги: {', '.join([s.value for s in steps])}\n\n"
                "Теперь вы можете использовать его в меню \"Мои сохраненные пресеты\"",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 К конструктору", callback_data=f"custom_pipeline_{vk_chat_id}_{date}")
                ]])
            )
            
        except Exception as e:
            logger.error(f"Ошибка в handle_preset_name_input: {e}", exc_info=True)
            await update.message.reply_text(format_error_message(e))

