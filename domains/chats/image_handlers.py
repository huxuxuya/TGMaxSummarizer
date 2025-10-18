"""
Обработчики для работы с анализом изображений
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .image_analysis_service import ImageAnalysisService
from .repository import MessageRepository
from shared.utils import format_success_message, format_error_message
import logging
import asyncio

logger = logging.getLogger(__name__)

class ImageAnalysisHandlers:
    """Обработчики для анализа изображений"""
    
    def __init__(self, 
                 image_analysis_service: ImageAnalysisService,
                 message_repository: MessageRepository):
        self.image_analysis_service = image_analysis_service
        self.message_repository = message_repository
    
    async def image_analysis_menu_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик меню анализа изображений"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('image_analysis_menu_', '', 1)
            
            # Получаем статистику
            stats = self.message_repository.get_chat_stats(vk_chat_id)
            
            text = f"🖼️ *[Анализ изображений]*\n\n"
            text += f"📊 *Статистика:*\n"
            text += f"• Всего изображений: {stats.total_images}\n"
            text += f"• Проанализировано: {stats.analyzed_images}\n"
            text += f"• Не проанализировано: {stats.unanalyzed_images}\n"
            
            # Получаем информацию о фото расписания для группы
            selected_group_id = context.user_data.get('selected_group_id')
            if selected_group_id:
                from core.app_context import get_app_context
                from .repository import ScheduleAnalysisRepository
                
                ctx = get_app_context()
                schedule_photo = ctx.chat_service.get_schedule_photo(selected_group_id)
                schedule_analysis_repo = ScheduleAnalysisRepository(ctx.db_connection)
                schedule_analysis = schedule_analysis_repo.get_schedule_analysis(selected_group_id) if schedule_photo else None
                
                if schedule_photo:
                    status = "✅ Проанализировано" if schedule_analysis else "❌ Не проанализировано"
                    text += f"\n📅 Фото расписания: {status}\n"
            
            if stats.unanalyzed_images > 0:
                text += f"\n⚠️ Есть {stats.unanalyzed_images} непроанализированных изображений.\n"
                text += "Нажмите 'Начать анализ' для обработки."
            else:
                text += f"\n✅ Все изображения проанализированы!"
            
            from infrastructure.telegram import keyboards
            has_schedule = selected_group_id and ctx.chat_service.get_schedule_photo(selected_group_id) is not None
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в image_analysis_menu_handler: {e}")
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('image_analysis_menu_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def start_image_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик запуска анализа изображений"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('start_image_analysis_', '', 1)
            
            # Получаем неанализированные сообщения
            unanalyzed_messages = await self.image_analysis_service.get_unanalyzed_messages(
                vk_chat_id, 
                self.message_repository
            )
            
            if not unanalyzed_messages:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
                await query.edit_message_text(
                    "✅ Все изображения уже проанализированы!",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                return
            
            total_images = sum(len(msg.image_paths) for msg in unanalyzed_messages)
            
            # Начальное сообщение
            await query.edit_message_text(
                f"🔄 Начинаем анализ...\n\n"
                f"📊 Сообщений для обработки: {len(unanalyzed_messages)}\n"
                f"🖼️ Всего изображений: {total_images}\n\n"
                f"⏳ Пожалуйста, подождите...",
                parse_mode='Markdown'
            )
            
            # Получаем настройки модели и промпта из context.user_data или используем дефолтные
            model = context.user_data.get('image_analysis_model')
            prompt = context.user_data.get('image_analysis_prompt')
            
            # Callback для обновления прогресса
            last_update_time = asyncio.get_event_loop().time()
            
            async def progress_callback(current, total, stats):
                nonlocal last_update_time
                current_time = asyncio.get_event_loop().time()
                
                # Обновляем каждые 5 секунд или каждые 5 сообщений
                if current_time - last_update_time >= 5 or current % 5 == 0 or current == total:
                    last_update_time = current_time
                    
                    progress_text = f"🔄 [Анализ изображений]...\n\n"
                    progress_text += f"📊 Прогресс: {current}/{total} сообщений\n"
                    progress_text += f"✅ Проанализировано: {stats['analyzed_images']} изображений\n"
                    progress_text += f"❌ Ошибок: {stats['failed_images']}\n\n"
                    progress_text += f"⏳ Пожалуйста, подождите..."
                    
                    try:
                        await query.edit_message_text(
                            progress_text,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.debug(f"Ошибка обновления прогресса: {e}")
            
            # Запускаем анализ
            result_stats = await self.image_analysis_service.analyze_chat_images(
                vk_chat_id,
                self.message_repository,
                model=model,
                prompt=prompt,
                progress_callback=progress_callback
            )
            
            # Анализируем фото расписания, если оно есть и не проанализировано
            selected_group_id = context.user_data.get('selected_group_id')
            schedule_analyzed = False
            if selected_group_id:
                from core.app_context import get_app_context
                from .repository import ScheduleAnalysisRepository
                
                ctx = get_app_context()
                schedule_photo = ctx.chat_service.get_schedule_photo(selected_group_id)
                
                if schedule_photo:
                    # Проверяем, проанализировано ли уже расписание
                    schedule_analysis_repo = ScheduleAnalysisRepository(ctx.db_connection)
                    existing_analysis = schedule_analysis_repo.get_schedule_analysis(selected_group_id)
                    
                    if not existing_analysis:
                        # Анализируем фото расписания только если оно не проанализировано
                        analysis_result = await self.image_analysis_service.analyze_schedule_photo(
                            schedule_photo, 
                            context.bot,
                            model=model,
                            prompt="Распознай текст расписания занятий. Укажи все уроки, время и другую информацию. Опиши структуру расписания подробно."
                        )
                        
                        if analysis_result:
                            schedule_analysis_repo.save_schedule_analysis(
                                selected_group_id,
                                schedule_photo,
                                analysis_result,
                                model or self.image_analysis_service.default_model
                            )
                            schedule_analyzed = True
            
            # Итоговое сообщение
            success_text = f"✅ *Анализ завершен!*\n\n"
            success_text += f"📊 *Результаты:*\n"
            success_text += f"• Обработано сообщений: {result_stats['total_messages']}\n"
            success_text += f"• Всего изображений: {result_stats['total_images']}\n"
            success_text += f"• Успешно проанализировано: {result_stats['analyzed_images']}\n"
            success_text += f"• Ошибок: {result_stats['failed_images']}\n"
            success_text += f"• Время обработки: {result_stats['processing_time']:.1f} сек\n"
            
            if schedule_analyzed:
                success_text += f"\n📅 *Фото расписания также проанализировано!*"
            
            from infrastructure.telegram import keyboards
            # Проверяем, есть ли анализ расписания для отображения кнопки
            has_schedule_analysis = False
            if selected_group_id:
                try:
                    existing_analysis = schedule_analysis_repo.get_schedule_analysis(selected_group_id)
                    has_schedule_analysis = existing_analysis is not None
                except:
                    pass
            
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=has_schedule_analysis)
            
            await query.edit_message_text(
                success_text,
                reply_markup=keyboard,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Ошибка в start_image_analysis_handler: {e}")
            import traceback
            traceback.print_exc()
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('start_image_analysis_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def image_analysis_settings_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик настроек анализа изображений"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('image_analysis_settings_', '', 1)
            
            current_model = context.user_data.get('image_analysis_model', 
                                                  self.image_analysis_service.default_model)
            current_prompt = context.user_data.get('image_analysis_prompt', 
                                                   self.image_analysis_service.default_prompt)
            
            text = f"⚙️ *[Настройки анализа изображений]*\n\n"
            text += f"🤖 Текущая модель: `{current_model}`\n\n"
            text += f"📝 Текущий промпт:\n`{current_prompt[:100]}...`\n"
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.image_analysis_settings_keyboard(vk_chat_id)
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в image_analysis_settings_handler: {e}")
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('image_analysis_settings_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def select_analysis_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик выбора модели для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('select_analysis_model_', '', 1)
            
            # Получаем список доступных моделей
            available_models = await self.image_analysis_service.get_available_models()
            
            if not available_models:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
                await query.edit_message_text(
                    "❌ Не удалось получить список моделей из Ollama.\n"
                    "Проверьте, что сервер Ollama доступен.",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                return
            
            # Создаем клавиатуру с моделями
            keyboard = []
            for model in available_models[:10]:  # Ограничиваем 10 моделями
                keyboard.append([InlineKeyboardButton(
                    f"🤖 {model}",
                    callback_data=f"set_analysis_model_{vk_chat_id}_{model}"
                )])
            
            keyboard.append([InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"image_analysis_settings_{vk_chat_id}"
            )])
            
            await query.edit_message_text(
                "🤖 [Выберите модель] для анализа изображений:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в select_analysis_model_handler: {e}")
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('select_analysis_model_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def set_analysis_model_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик установки модели для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Парсим данные: set_analysis_model_{vk_chat_id}_{model}
            parts = query.data.replace('set_analysis_model_', '', 1).split('_', 1)
            if len(parts) < 2:
                raise ValueError("Некорректный формат callback_data")
            
            vk_chat_id = parts[0]
            model = parts[1]
            
            # Сохраняем выбор в context.user_data
            context.user_data['image_analysis_model'] = model
            
            await query.edit_message_text(
                f"✅ Модель установлена: `{model}`",
                parse_mode='Markdown'
            )
            
            # Через 2 секунды возвращаемся к меню настроек
            await asyncio.sleep(2)
            
            from infrastructure.telegram import keyboards
            keyboard = keyboards.image_analysis_settings_keyboard(vk_chat_id)
            
            current_prompt = context.user_data.get('image_analysis_prompt', 
                                                   self.image_analysis_service.default_prompt)
            
            text = f"⚙️ *[Настройки анализа изображений]*\n\n"
            text += f"🤖 Текущая модель: `{model}`\n\n"
            text += f"📝 Текущий промпт:\n`{current_prompt[:100]}...`\n"
            
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в set_analysis_model_handler: {e}")
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('set_analysis_model_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def change_analysis_prompt_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик изменения промпта для анализа"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('change_analysis_prompt_', '', 1)
            
            # Сохраняем vk_chat_id для последующего использования
            context.user_data['pending_prompt_change_chat_id'] = vk_chat_id
            
            await query.edit_message_text(
                "📝 Отправьте новый промпт для анализа изображений.\n\n"
                "Пример:\n"
                "`Опиши детально что изображено на этой фотографии, включая людей, объекты и обстановку.`\n\n"
                "Или отправьте /cancel для отмены.",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка в change_analysis_prompt_handler: {e}")
            from infrastructure.telegram import keyboards
            vk_chat_id = query.data.replace('change_analysis_prompt_', '', 1)
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )
    
    async def show_schedule_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать результат анализа фото расписания"""
        query = update.callback_query
        await query.answer()
        
        try:
            vk_chat_id = query.data.replace('show_schedule_analysis_', '', 1)
            selected_group_id = context.user_data.get('selected_group_id')
            
            if not selected_group_id:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
                await query.edit_message_text(
                    "❌ Группа не выбрана",
                    reply_markup=keyboard
                )
                return
            
            # Получить анализ из базы
            from core.app_context import get_app_context
            from .repository import ScheduleAnalysisRepository
            
            ctx = get_app_context()
            schedule_analysis_repo = ScheduleAnalysisRepository(ctx.db_connection)
            schedule_analysis = schedule_analysis_repo.get_schedule_analysis(selected_group_id)
            
            if schedule_analysis:
                from infrastructure.telegram.formatter import TelegramFormatter
                
                text = f"📅 *[Анализ расписания]*\n\n"
                text += f"🤖 Модель: {TelegramFormatter.escape_markdown_v1(schedule_analysis['model_used'])}\n"
                text += f"📅 Дата анализа: {TelegramFormatter.escape_markdown_v1(str(schedule_analysis['analysis_date']))}\n\n"
                text += f"📝 *Распознанный текст:*\n{TelegramFormatter.escape_markdown_v1(schedule_analysis['analysis_text'])}"
                
                from infrastructure.telegram import keyboards
                keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=True)
                
                await query.edit_message_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
            else:
                from infrastructure.telegram import keyboards
                keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
                await query.edit_message_text(
                    "❌ Расписание не проанализировано",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Ошибка в show_schedule_analysis_handler: {e}")
            from infrastructure.telegram import keyboards
            keyboard = keyboards.image_analysis_menu_keyboard(vk_chat_id, has_schedule=False)
            
            # Если это ошибка парсинга Markdown, попробуем отправить без Markdown
            if "can't parse entities" in str(e) or "can't find end of the entity" in str(e):
                try:
                    # Получаем данные еще раз и отправляем без Markdown
                    selected_group_id = context.user_data.get('selected_group_id')
                    if selected_group_id:
                        from core.app_context import get_app_context
                        from .repository import ScheduleAnalysisRepository
                        
                        ctx = get_app_context()
                        schedule_analysis_repo = ScheduleAnalysisRepository(ctx.db_connection)
                        schedule_analysis = schedule_analysis_repo.get_schedule_analysis(selected_group_id)
                        
                        if schedule_analysis:
                            text = f"📅 Анализ расписания\n\n"
                            text += f"🤖 Модель: {schedule_analysis['model_used']}\n"
                            text += f"📅 Дата анализа: {schedule_analysis['analysis_date']}\n\n"
                            text += f"📝 Распознанный текст:\n{schedule_analysis['analysis_text']}"
                            
                            await query.edit_message_text(
                                text,
                                reply_markup=keyboard
                            )
                            return
                except Exception as fallback_error:
                    logger.error(f"Ошибка в fallback обработке: {fallback_error}")
            
            await query.edit_message_text(
                format_error_message(e),
                reply_markup=keyboard
            )

