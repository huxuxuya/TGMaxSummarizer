from telegram import Update
from telegram.ext import ContextTypes
from .service import AIService
from .models import AnalysisRequest, AnalysisType
from shared.utils import format_success_message, format_error_message, shorten_callback_data
from shared.constants import CallbackActions
import logging

logger = logging.getLogger(__name__)

class AIHandlers:
    """Обработчики для работы с AI провайдерами"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def select_ai_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора AI провайдера"""
        query = update.callback_query
        await query.answer()
        
        try:
            available_providers = await self.ai_service.get_available_providers()
            provider_names = [p.name for p in available_providers]
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.ai_provider_selection_keyboard(provider_names, provider_info=available_providers)
            
            await query.edit_message_text(
                "🤖 Выбор AI провайдера\n\n"
                "Выберите провайдер для анализа чатов:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_ai_provider_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретного провайдера"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(':')[-1]
            context.user_data['selected_provider'] = provider_name
            
            if provider_name == 'openrouter':
                await self._handle_openrouter_selection(update, context)
            elif provider_name == 'ollama':
                await self._handle_ollama_selection(update, context)
            else:
                await self._confirm_provider_selection(update, context, provider_name)
                
        except Exception as e:
            logger.error(f"Ошибка в select_provider_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def _handle_openrouter_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора OpenRouter"""
        query = update.callback_query
        
        try:
            from infrastructure.ai_providers.providers.openrouter import OpenRouterProvider
            from core.config import load_config
            
            config = load_config()
            provider = OpenRouterProvider(config['ai'].providers['openrouter'].dict())
            
            if not await provider.initialize():
                await query.edit_message_text(
                    "❌ OpenRouter недоступен"
                )
                return
            
            available_models = await provider.get_available_models()
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.openrouter_model_selection_keyboard(available_models)
            
            await query.edit_message_text(
                "🔗 Выбор модели OpenRouter\n\n"
                "Выберите модель для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_openrouter_selection: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def _handle_ollama_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора Ollama"""
        query = update.callback_query
        
        try:
            from infrastructure.ai_providers.providers.ollama import OllamaProvider
            from core.config import load_config
            
            config = load_config()
            provider = OllamaProvider(config['ai'].providers['ollama'].dict())
            
            if not await provider.initialize():
                await query.edit_message_text(
                    "❌ Ollama недоступен"
                )
                return
            
            available_models = await provider.get_available_models()
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.ollama_model_selection_keyboard(available_models)
            
            await query.edit_message_text(
                "🦙 Выбор модели Ollama\n\n"
                "Выберите модель для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _handle_ollama_selection: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def _confirm_provider_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, provider_name: str):
        """Подтверждение выбора провайдера"""
        query = update.callback_query
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.confirm_ai_provider_change_keyboard(provider_name)
            
            provider_display_names = {
                'gigachat': 'GigaChat',
                'chatgpt': 'ChatGPT',
                'gemini': 'Gemini'
            }
            
            display_name = provider_display_names.get(provider_name, provider_name.title())
            
            await query.edit_message_text(
                f"🤖 Подтверждение выбора\n\n"
                f"Вы хотите использовать {display_name} для анализа чатов?",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в _confirm_provider_selection: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def confirm_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения выбора провайдера"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(':')[-1]
            context.user_data['confirmed_provider'] = provider_name
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            provider_display_names = {
                'gigachat': 'GigaChat',
                'chatgpt': 'ChatGPT',
                'openrouter': 'OpenRouter',
                'gemini': 'Gemini',
                'ollama': 'Ollama'
            }
            
            display_name = provider_display_names.get(provider_name, provider_name.title())
            
            await query.edit_message_text(
                format_success_message(
                    f"Провайдер {display_name} выбран для анализа чатов"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в confirm_provider_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_model_for_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора модели для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = context.user_data.get('selected_chat_id')
            if not vk_chat_id:
                await query.edit_message_text(
                    "❌ Чат не выбран"
                )
                return
            
            from infrastructure.telegram import keyboards
            available_providers = await self.ai_service.get_available_providers()
            provider_names = [p.name for p in available_providers]
            keyboard = keyboards.ai_provider_selection_keyboard(provider_names, provider_info=available_providers)
            
            await query.edit_message_text(
                "🤖 Выбор модели для анализа\n\n"
                "Выберите AI провайдер и модель:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_model_for_analysis_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def run_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик запуска анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = context.user_data.get('selected_chat_id')
            date = context.user_data.get('selected_date')
            provider_name = context.user_data.get('confirmed_provider')
            model_id = context.user_data.get('selected_model_id')
            
            if not all([vk_chat_id, date, provider_name]):
                await query.edit_message_text(
                    "❌ Не все параметры выбраны для анализа"
                )
                return
            
            await query.edit_message_text(
                "🤖 Запуск анализа...\n\n"
                "Это может занять несколько минут."
            )
            
            from domains.chats.service import ChatService
            from core.database.connection import DatabaseConnection
            from core.config import load_config
            
            config = load_config()
            db_connection = DatabaseConnection(config['database'].path)
            chat_service = ChatService(db_connection)
            
            messages = chat_service.get_messages_by_date(vk_chat_id, date)
            
            if not messages:
                await query.edit_message_text(
                    "❌ Нет сообщений для анализа"
                )
                return
            
            messages_data = [msg.dict() for msg in messages]
            
            analysis_request = AnalysisRequest(
                messages=messages_data,
                provider_name=provider_name,
                model_id=model_id,
                user_id=update.effective_user.id,
                analysis_type=AnalysisType.SUMMARIZATION
            )
            
            result = await self.ai_service.analyze_chat(analysis_request)
            
            if result.success:
                from domains.summaries.service import SummaryService
                from domains.summaries.models import Summary, SummaryType
                
                summary_service = SummaryService(db_connection)
                
                summary = Summary(
                    vk_chat_id=vk_chat_id,
                    date=date,
                    summary_text=result.result,
                    provider_name=result.provider_name,
                    processing_time=result.processing_time
                )
                
                summary_service.save_summary(summary)
                
                await query.edit_message_text(
                    format_success_message(
                        f"Анализ завершен за {result.processing_time:.2f}с\n\n"
                        f"Результат:\n{result.result[:500]}..."
                    )
                )
            else:
                await query.edit_message_text(
                    f"❌ Ошибка анализа: {result.error}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка в run_analysis_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def ai_provider_settings_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек AI провайдеров"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.ai_provider_settings_keyboard()
            
            await query.edit_message_text(
                "⚙️ Настройки AI провайдеров\n\n"
                "Выберите действие:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в ai_provider_settings_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def ai_provider_defaults_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек по умолчанию"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            # TODO: Get current default from user preferences
            current_default = 'gigachat'
            keyboard = keyboards.ai_provider_defaults_keyboard(current_default)
            
            await query.edit_message_text(
                "⚙️ Провайдер по умолчанию\n\n"
                "Выберите провайдер, который будет использоваться по умолчанию:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в ai_provider_defaults_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def ai_provider_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик статуса провайдеров"""
        query = update.callback_query
        await query.answer()
        
        try:
            available_providers = await self.ai_service.get_available_providers()
            
            status_text = "📊 Статус AI провайдеров:\n\n"
            for provider in available_providers:
                status_icon = "✅" if provider.available else "❌"
                status_text += f"{status_icon} {provider.name}\n"
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            await query.edit_message_text(
                status_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в ai_provider_status_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def check_providers_availability_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик проверки доступности провайдеров"""
        query = update.callback_query
        await query.answer()
        
        try:
            await query.edit_message_text(
                "🔍 Проверка доступности провайдеров...\n\n"
                "Это может занять несколько секунд."
            )
            
            # TODO: Implement actual availability check
            available_providers = await self.ai_service.get_available_providers()
            
            status_text = "📊 Результаты проверки:\n\n"
            for provider in available_providers:
                status_icon = "✅" if provider.available else "❌"
                status_text += f"{status_icon} {provider.name}\n"
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            await query.edit_message_text(
                status_text,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в check_providers_availability_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def openrouter_model_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора моделей OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.ai_providers.providers.openrouter import OpenRouterProvider
            from core.config import load_config
            
            config = load_config()
            provider = OpenRouterProvider(config['ai'].providers['openrouter'].dict())
            
            if not await provider.initialize():
                await query.edit_message_text(
                    "❌ OpenRouter недоступен"
                )
                return
            
            available_models = await provider.get_available_models()
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.openrouter_model_selection_keyboard(available_models)
            
            await query.edit_message_text(
                "🔗 Выбор модели OpenRouter\n\n"
                "Выберите модель для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в openrouter_model_selection_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_openrouter_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретной модели OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(':')[-1]
            context.user_data['selected_model_id'] = model_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.openrouter_model_info_keyboard(model_id)
            
            await query.edit_message_text(
                f"🔗 Модель: {model_id}\n\n"
                "Подтвердите выбор модели:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_openrouter_model_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def confirm_openrouter_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения выбора модели OpenRouter"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(':')[-1]
            context.user_data['confirmed_model'] = model_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            await query.edit_message_text(
                format_success_message(
                    f"Модель OpenRouter {model_id} выбрана для анализа"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в confirm_openrouter_model_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def top5_models_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора топ-5 моделей"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.telegram import keyboards
            keyboard = keyboards.top5_models_keyboard()
            
            await query.edit_message_text(
                "🏆 Топ-5 лучших моделей\n\n"
                "Выберите одну из рекомендуемых моделей:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в top5_models_selection_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_top5_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретной топ-5 модели"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(':')[-1]
            context.user_data['selected_model_id'] = model_id
            
            # Extract model name from ID for display
            model_name = model_id.split('/')[-1] if '/' in model_id else model_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.top5_model_info_keyboard(model_id, model_name)
            
            await query.edit_message_text(
                f"🏆 Модель: {model_name}\n\n"
                "Подтвердите выбор модели:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_top5_model_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def confirm_top5_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик подтверждения выбора топ-5 модели"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_id = query.data.split(':')[-1]
            context.user_data['confirmed_model'] = model_id
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            model_name = model_id.split('/')[-1] if '/' in model_id else model_id
            
            await query.edit_message_text(
                format_success_message(
                    f"Модель {model_name} выбрана для анализа"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в confirm_top5_model_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def ollama_model_selection_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора моделей Ollama"""
        query = update.callback_query
        await query.answer()
        
        try:
            from infrastructure.ai_providers.providers.ollama import OllamaProvider
            from core.config import load_config
            
            config = load_config()
            provider = OllamaProvider(config['ai'].providers['ollama'].dict())
            
            if not await provider.initialize():
                await query.edit_message_text(
                    "❌ Ollama недоступен"
                )
                return
            
            available_models = await provider.get_available_models()
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.ollama_model_selection_keyboard(available_models)
            
            await query.edit_message_text(
                "🦙 Выбор модели Ollama\n\n"
                "Выберите модель для анализа:",
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в ollama_model_selection_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def select_ollama_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора конкретной модели Ollama"""
        query = update.callback_query
        await query.answer()
        
        try:
            model_name = query.data.split(':')[-1]
            context.user_data['selected_model_id'] = model_name
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.back_keyboard()
            
            await query.edit_message_text(
                format_success_message(
                    f"Модель Ollama {model_name} выбрана для анализа"
                ),
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_ollama_model_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )
    
    async def analyze_with_provider_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик анализа с выбранным провайдером"""
        query = update.callback_query
        await query.answer()
        
        try:
            provider_name = query.data.split(':')[-1]
            context.user_data['selected_provider'] = provider_name
            
            vk_chat_id = context.user_data.get('selected_chat_id')
            if not vk_chat_id:
                await query.edit_message_text(
                    "❌ Чат не выбран"
                )
                return
            
            # Redirect to model selection based on provider
            if provider_name == 'openrouter':
                await self.openrouter_model_selection_handler(update, context)
            elif provider_name == 'ollama':
                await self.ollama_model_selection_handler(update, context)
            else:
                # For other providers, confirm directly
                await self._confirm_provider_selection(update, context, provider_name)
                
        except Exception as e:
            logger.error(f"Ошибка в analyze_with_provider_handler: {e}")
            await query.edit_message_text(
                format_error_message(e)
            )

