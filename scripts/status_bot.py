#!/usr/bin/env python3
"""
📊 СКРИПТ ПРОВЕРКИ СТАТУСА TELEGRAM БОТА
Показывает статус бота и конфигурацию
Запуск: python status_bot.py
"""
import os
import sys
import subprocess
import psutil
from pathlib import Path

def main():
    """Главная функция проверки статуса"""
    print("📊 СТАТУС TELEGRAM БОТА")
    print("=" * 30)
    
    # Получаем директорию проекта
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    # Проверяем конфигурацию
    print("🔧 ПРОВЕРКА КОНФИГУРАЦИИ:")
    
    # Проверяем переменные окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    vk_max_token = os.getenv("VK_MAX_TOKEN")
    gigachat_key = os.getenv("GIGACHAT_API_KEY")
    
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Установлен' if telegram_token else '❌ Не установлен'}")
    print(f"   VK_MAX_TOKEN: {'✅ Установлен' if vk_max_token else '❌ Не установлен'}")
    print(f"   GIGACHAT_API_KEY: {'✅ Установлен' if gigachat_key else '❌ Не установлен'}")
    
    # Проверяем файлы конфигурации
    config_files = [".env", "bot_config.env", "telegram_bot/.env"]
    config_found = False
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   📁 Файл конфигурации: {config_file}")
            config_found = True
            break
    
    if not config_found:
        print("   ❌ Файл конфигурации не найден")
    
    print("\n🔍 ПРОВЕРКА ПРОЦЕССОВ:")
    
    # Ищем процессы бота
    bot_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if any(script in cmdline for script in [
                        'start_with_tokens.py', 
                        'run_bot.py', 
                        'run_bot_stable.py',
                        'bot.py'
                    ]):
                        bot_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"❌ Ошибка поиска процессов: {e}")
        return 1
    
    if bot_processes:
        print(f"✅ Найдено {len(bot_processes)} активных процессов бота:")
        for proc in bot_processes:
            try:
                create_time = proc.create_time()
                print(f"   🔸 PID {proc.info['pid']} - запущен {create_time}")
            except:
                print(f"   🔸 PID {proc.info['pid']} - информация недоступна")
    else:
        print("❌ Активные процессы бота не найдены")
    
    print("\n📦 ПРОВЕРКА ЗАВИСИМОСТЕЙ:")
    
    # Проверяем зависимости
    dependencies = [
        'telegram', 'requests', 'websockets', 'python_max_client',
        'httpx', 'asyncio', 'sqlite3'
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n💡 Установите недостающие зависимости:")
        print(f"   pip install {' '.join(missing_deps)}")
    
    print("\n📁 ФАЙЛЫ ПРОЕКТА:")
    
    # Проверяем основные файлы
    main_files = [
        'bot.py', 'start_with_tokens.py', 'run_bot_stable.py',
        'vk_integration.py', 'chat_analyzer.py', 'database.py',
        'handlers.py', 'config.py', 'requirements.txt'
    ]
    
    for file in main_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
    
    print("\n🎯 РЕКОМЕНДАЦИИ:")
    
    if not telegram_token or not vk_max_token:
        print("   🔧 Установите переменные окружения или создайте .env файл")
    
    if missing_deps:
        print("   📦 Установите недостающие зависимости")
    
    if not bot_processes:
        print("   🚀 Запустите бота: python start_bot.py")
    else:
        print("   ✅ Бот уже запущен")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
