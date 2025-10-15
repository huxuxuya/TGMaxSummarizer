#!/usr/bin/env python3
"""
Скрипт для мониторинга логов бота в реальном времени
"""
import subprocess
import sys
import re
from datetime import datetime

def monitor_bot_logs():
    """Мониторинг логов бота для поиска ошибок форматирования"""
    
    print("🔍 Мониторинг логов бота...")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)
    
    try:
        # Запускаем бота и мониторим его вывод
        process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Ключевые слова для поиска
        error_patterns = [
            r"Can't parse entities",
            r"UNBALANCED BOLD TAGS",
            r"MARKDOWN_V2 DEBUG INFO",
            r"ERROR.*formatting",
            r"❌.*Ошибка"
        ]
        
        line_count = 0
        
        for line in iter(process.stdout.readline, ''):
            line_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Проверяем на ключевые паттерны
            for pattern in error_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    print(f"🚨 [{timestamp}] НАЙДЕНА ПРОБЛЕМА:")
                    print(f"   {line.strip()}")
                    print("-" * 40)
                    break
            else:
                # Обычные логи (только DEBUG и выше)
                if any(level in line for level in ["DEBUG", "INFO", "WARNING", "ERROR"]):
                    print(f"[{timestamp}] {line.strip()}")
            
            # Показываем прогресс каждые 100 строк
            if line_count % 100 == 0:
                print(f"📊 Обработано {line_count} строк логов...")
                
    except KeyboardInterrupt:
        print("\n⏹️ Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
    finally:
        if 'process' in locals():
            process.terminate()

def analyze_existing_logs():
    """Анализ существующих логов на предмет ошибок"""
    
    print("📋 Анализ существующих логов...")
    print("=" * 60)
    
    try:
        # Ищем файлы логов
        import glob
        log_files = glob.glob("*.log") + glob.glob("logs/*.log")
        
        if not log_files:
            print("❌ Файлы логов не найдены")
            return
        
        error_count = 0
        
        for log_file in log_files:
            print(f"\n📁 Анализ файла: {log_file}")
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines, 1):
                    if "Can't parse entities" in line:
                        print(f"   🚨 Строка {i}: {line.strip()}")
                        error_count += 1
                        
                        # Показываем контекст (5 строк до и после)
                        start = max(0, i - 6)
                        end = min(len(lines), i + 5)
                        print("   📝 Контекст:")
                        for j in range(start, end):
                            marker = ">>> " if j == i - 1 else "    "
                            print(f"   {marker}{j+1}: {lines[j].strip()}")
                        print()
                        
            except Exception as e:
                print(f"   ❌ Ошибка чтения файла: {e}")
        
        if error_count == 0:
            print("✅ Ошибок форматирования в логах не найдено")
        else:
            print(f"🚨 Найдено {error_count} ошибок форматирования")
            
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_existing_logs()
    else:
        monitor_bot_logs()
