#!/usr/bin/env python3
"""
⚡ БЫСТРЫЙ ЗАПУСК TELEGRAM БОТА
Минимальные проверки, быстрый запуск
Запуск: python quick_start.py
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Быстрый запуск бота"""
    print("⚡ БЫСТРЫЙ ЗАПУСК TELEGRAM БОТА")
    print("=" * 35)
    
    # Получаем директорию проекта
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    print("🚀 Запускаем бота...")
    
    # Запускаем бота напрямую
    try:
        # Импортируем и запускаем бота
        from bot import VKMaxTelegramBot
        import asyncio
        
        async def run_bot():
            bot = VKMaxTelegramBot()
            try:
                await bot.start_polling()
            except KeyboardInterrupt:
                print("\n👋 Бот остановлен пользователем")
            finally:
                await bot.stop()
        
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        if 'process' in locals():
            process.terminate()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
