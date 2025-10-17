import asyncio
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from core.app_context import get_app_context
from domains.handlers_manager import HandlersManager
from shared.constants import CallbackActions
from shared.validators import setup_development_validation

def setup_logging(config):
    """Настройка логирования"""
    logging.basicConfig(
        format=config['bot'].log_format,
        level=getattr(logging, config['bot'].log_level),
        datefmt="%H:%M:%S"
    )

class VKMaxTelegramBot:
    """Основной класс Telegram бота с новой архитектурой"""
    
    def __init__(self):
        self.ctx = get_app_context()
        self.handlers_manager = HandlersManager()
        self.application = None
        
        setup_logging(self.ctx.config)
        self.logger = logging.getLogger(__name__)
    
    def create_application(self):
        """Создать приложение Telegram"""
        # Оптимизированные настройки для быстрой работы
        self.application = Application.builder().token(
            self.ctx.config['bot'].telegram_bot_token
        ).connection_pool_size(8).read_timeout(30).write_timeout(30).connect_timeout(10).build()
        
        self.application.add_handler(CommandHandler("start", self.handlers_manager.start_handler))
        self.application.add_handler(CallbackQueryHandler(self.handlers_manager.callback_query_handler))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers_manager.message_handler))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handlers_manager.photo_handler))
        
        self.application.add_error_handler(self.error_handler)
        
        self.logger.info("✅ Обработчики зарегистрированы")
    
    async def error_handler(self, update: Update, context):
        """Обработчик ошибок"""
        self.logger.error(f"Ошибка при обработке обновления: {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуйте позже."
                )
            except Exception as e:
                self.logger.error(f"Ошибка отправки сообщения об ошибке: {e}")
    
    async def start_polling(self):
        """Запустить бота в режиме polling"""
        if not self.application:
            self.create_application()
        
        self.logger.info("🚀 Запуск Telegram бота...")
        
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("✅ Бот запущен и работает")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("🛑 Получен сигнал остановки")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска бота: {e}")
        finally:
            if self.application:
                try:
                    await self.application.stop()
                    await self.application.shutdown()
                except Exception as e:
                    self.logger.error(f"Ошибка при остановке: {e}")
    
    async def stop(self):
        """Остановить бота"""
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        # Cleanup app context
        self.ctx.shutdown()
        self.logger.info("🛑 Бот остановлен")

async def main():
    """Главная функция"""
    logger = logging.getLogger(__name__)
    
    # Setup development validation if enabled
    setup_development_validation()
    
    logger.info("🤖 Инициализация VK MAX Telegram Bot")
    
    ctx = get_app_context()
    if ctx.config['bot'].telegram_bot_token == "your_bot_token":
        logger.error("❌ Не установлен TELEGRAM_BOT_TOKEN")
        return
    
    if ctx.config['bot'].vk_max_token == "your_vk_max_token":
        logger.error("❌ Не установлен VK_MAX_TOKEN")
        return
    
    if not ctx.config['ai'].providers['gigachat'].api_key or ctx.config['ai'].providers['gigachat'].api_key == "your_gigachat_key":
        logger.warning("⚠️ Не установлен GIGACHAT_API_KEY - анализ чатов может быть недоступен")
    
    bot = VKMaxTelegramBot()
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
