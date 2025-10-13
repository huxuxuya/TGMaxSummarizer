#!/usr/bin/env python3
"""
Тест системы логирования LLM
"""
import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm_logger import LLMLogger
from chat_analyzer import ChatAnalyzer
from config import AI_PROVIDERS, ENABLE_LLM_LOGGING

async def test_llm_logging():
    """Тест системы логирования LLM"""
    print("🧪 Тестируем систему логирования LLM...")
    
    # Проверяем настройки
    print(f"📋 ENABLE_LLM_LOGGING: {ENABLE_LLM_LOGGING}")
    
    if not ENABLE_LLM_LOGGING:
        print("⚠️ Логирование LLM отключено в настройках")
        return False
    
    # Создаем тестовые сообщения
    test_messages = [
        {
            'message_time': 1697123456789,
            'sender_name': 'Иванова М.А.',
            'text': 'Добрый день! Напоминаю про родительское собрание завтра в 18:00.'
        },
        {
            'message_time': 1697123516789,
            'sender_name': 'Петров С.В.',
            'text': 'Подскажите, когда сдавать деньги на экскурсию?'
        },
        {
            'message_time': 1697123576789,
            'sender_name': 'Сидорова А.И.',
            'text': 'Деньги нужно сдать до пятницы.'
        }
    ]
    
    # Создаем анализатор
    analyzer = ChatAnalyzer()
    
    # Тестируем с Ollama провайдером (если доступен)
    print("🤖 Тестируем с Ollama провайдером...")
    
    try:
        result = await analyzer.analyze_chat_with_specific_model(
            messages=test_messages,
            provider_name='ollama',
            model_id='gpt-oss:20b',
            user_id=12345
        )
        
        if result:
            print("✅ Анализ завершен успешно")
            print(f"📊 Результат: {type(result)}")
            
            if isinstance(result, dict):
                print(f"   - Суммаризация: {'✅' if result.get('summary') else '❌'}")
                print(f"   - Рефлексия: {'✅' if result.get('reflection') else '❌'}")
                print(f"   - Улучшение: {'✅' if result.get('improved') else '❌'}")
            
            # Проверяем создание файлов логов
            logs_dir = "llm_logs"
            today = datetime.now().strftime("%Y-%m-%d")
            date_dir = os.path.join(logs_dir, today)
            
            if os.path.exists(date_dir):
                print(f"📁 Папка логов создана: {date_dir}")
                
                # Проверяем файлы
                expected_files = [
                    "01_formatted_messages.txt",
                    "02_summarization_request.txt", 
                    "03_summarization_response.txt",
                    "08_raw_result.txt",
                    "09_formatted_result.txt",
                    "00_session_summary.txt"
                ]
                
                created_files = []
                for filename in expected_files:
                    filepath = os.path.join(date_dir, filename)
                    if os.path.exists(filepath):
                        created_files.append(filename)
                        print(f"   ✅ {filename}")
                    else:
                        print(f"   ❌ {filename} - не найден")
                
                print(f"📊 Создано файлов: {len(created_files)}/{len(expected_files)}")
                
                # Показываем содержимое одного файла для проверки
                if created_files:
                    sample_file = os.path.join(date_dir, created_files[0])
                    print(f"\n📄 Содержимое {created_files[0]}:")
                    print("-" * 50)
                    try:
                        with open(sample_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print(content[:500] + "..." if len(content) > 500 else content)
                    except Exception as e:
                        print(f"❌ Ошибка чтения файла: {e}")
                    print("-" * 50)
                
                return len(created_files) >= 3  # Минимум 3 файла должны быть созданы
            else:
                print(f"❌ Папка логов не создана: {date_dir}")
                return False
        else:
            print("❌ Анализ не выполнен")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Основная функция"""
    print("🚀 Запуск теста системы логирования LLM...")
    
    try:
        success = await test_llm_logging()
        if success:
            print("\n🎉 Тест системы логирования завершен успешно!")
        else:
            print("\n💥 Тест системы логирования завершился с ошибками!")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
