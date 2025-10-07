#!/usr/bin/env python3
"""
🛑 СКРИПТ ОСТАНОВКИ TELEGRAM БОТА
Останавливает все запущенные экземпляры бота
Запуск: python stop_bot.py
"""
import os
import sys
import subprocess
import signal
import psutil
from pathlib import Path

def main():
    """Главная функция остановки"""
    print("🛑 ОСТАНОВКА TELEGRAM БОТА")
    print("=" * 30)
    
    # Получаем директорию проекта
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    # Ищем процессы бота
    bot_processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
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
                        print(f"🔍 Найден процесс бота: PID {proc.info['pid']} - {cmdline}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        print(f"❌ Ошибка поиска процессов: {e}")
        return 1
    
    if not bot_processes:
        print("✅ Процессы бота не найдены")
        return 0
    
    print(f"📋 Найдено {len(bot_processes)} процессов бота")
    
    # Останавливаем процессы
    stopped_count = 0
    for proc in bot_processes:
        try:
            print(f"🛑 Останавливаем процесс {proc.info['pid']}...")
            proc.terminate()
            
            # Ждем завершения процесса
            try:
                proc.wait(timeout=5)
                print(f"✅ Процесс {proc.info['pid']} остановлен")
                stopped_count += 1
            except psutil.TimeoutExpired:
                print(f"⚠️  Принудительно завершаем процесс {proc.info['pid']}...")
                proc.kill()
                print(f"✅ Процесс {proc.info['pid']} принудительно завершен")
                stopped_count += 1
                
        except psutil.NoSuchProcess:
            print(f"✅ Процесс {proc.info['pid']} уже завершен")
            stopped_count += 1
        except Exception as e:
            print(f"❌ Ошибка остановки процесса {proc.info['pid']}: {e}")
    
    print(f"🎉 Остановлено {stopped_count} процессов бота")
    return 0

if __name__ == "__main__":
    sys.exit(main())
