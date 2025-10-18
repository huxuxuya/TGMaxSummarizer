from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .service import SummaryService
from .models import SummaryType
from shared.utils import format_success_message, format_error_message, format_date_for_display
from shared.constants import CallbackActions
import logging

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
            
            # Отправляем первую часть с кнопками
            await query.edit_message_text(
                message_parts[0],
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            # Отправляем остальные части без кнопок
            for part in message_parts[1:]:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=part,
                    disable_web_page_preview=True
                )
            
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
            from infrastructure.telegram.sender import ParseMode
            from shared.utils import format_summary_for_telegram_html_universal
            
            if use_html:
                formatted_parts = format_summary_for_telegram_html_universal(
                    summary.summary_text, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = ParseMode.HTML
            else:
                from shared.utils import format_summary_for_telegram
                formatted_parts = format_summary_for_telegram(
                    summary.summary_text, 
                    date, 
                    summary.vk_chat_id
                )
                parse_mode = ParseMode.MARKDOWN_V2
            
            for part in formatted_parts:
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
            from infrastructure.logging.llm_logger import LLMLogger
            import os
            
            LLM_LOGS_DIR = os.environ.get('LLM_LOGS_DIR', 'llm_logs')
            print(f"🔍 DEBUG: Создаем LLM Logger с параметрами:")
            print(f"   LLM_LOGS_DIR: {LLM_LOGS_DIR}")
            print(f"   date: {date}")
            print(f"   scenario: {scenario}")
            print(f"   model: {model}")
            print(f"   user_id: {query.from_user.id}")
            
            llm_logger = LLMLogger(
                LLM_LOGS_DIR, 
                date=date, 
                scenario=scenario,
                test_mode=False,
                model_name=model
            )
            llm_logger.set_session_info(provider, model, None, query.from_user.id)
            logs_path = llm_logger.get_logs_path()
            print(f"🔍 DEBUG: LLM Logger создан, путь к логам: {logs_path}")
            logger.info(f"📁 LLM Logger создан: {logs_path}")
            
            analysis_request = AnalysisRequest(
                messages=messages_data,
                provider_name=provider,
                model_id=model,
                user_id=query.from_user.id,
                analysis_type=analysis_type,  # ✅ ПРАВИЛЬНО
                clean_data_first=clean_data_first,  # ✅ Для сценария cleaning
                llm_logger=llm_logger
            )
            
            # Выполняем анализ
            result = await ai_service.analyze_chat(analysis_request)
            
            if result.success:
                # Сохраняем результат
                summary = Summary(
                    vk_chat_id=vk_chat_id,
                    date=date,
                    summary_text=result.result,
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
                
                # Формируем полный текст результата
                result_text = f"✅ Анализ завершен за {result.processing_time:.2f}с\n\n"
                result_text += f"📋 Сценарий: {scenario_names.get(scenario, scenario)}\n"
                result_text += f"🤖 Провайдер: {result.provider_name}\n"
                result_text += f"🧠 Модель: {model}\n"
                result_text += f"📅 Дата: {date}\n\n"
                result_text += f"📝 Результат:\n{result.result}"
                
                # Разбиваем на части если нужно
                from shared.utils import format_message_for_telegram
                message_parts = format_message_for_telegram(result_text)
                
                # Отправляем первую часть с кнопками
                await query.edit_message_text(
                    format_success_message(message_parts[0]),
                    reply_markup=keyboard,
                    disable_web_page_preview=True
                )
                
                # Отправляем остальные части без кнопок
                for part in message_parts[1:]:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=part,
                        disable_web_page_preview=True
                    )
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

