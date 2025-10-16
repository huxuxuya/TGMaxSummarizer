#!/usr/bin/env python3
"""
Тест логирования для разных моделей
"""
import os
import asyncio
import logging

# Устанавливаем переменные окружения
os.environ['OLLAMA_BASE_URL'] = 'http://192.168.1.75:11434'
os.environ['TEST_MODE'] = 'true'
os.environ['ENABLE_LLM_LOGGING'] = 'true'
os.environ['OLLAMA_TIMEOUT'] = '600'

from database import DatabaseManager
from chat_analyzer import ChatAnalyzer
from config import AI_PROVIDERS
from llm_logger import LLMLogger

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_logging_for_model(model_name: str):
    """Тестируем логирование для конкретной модели"""
    print(f"\n🧪 Тестирование логирования для модели: {model_name}")
    print("=" * 60)
    
    try:
        # Устанавливаем модель для теста
        os.environ['TEST_MODEL_NAME'] = model_name
        
        # Получаем данные из БД
        db = DatabaseManager('bot_database.db')
        all_groups = db.get_all_groups()
        
        if not all_groups:
            print("❌ Нет групп в базе данных")
            return False
        
        # Берем первую группу
        chat_info = all_groups[0]
        group_id = chat_info['group_id']
        chat_name = chat_info.get('group_name', 'Unknown')
        
        print(f"📱 Используется группа: {chat_name} (ID: {group_id})")
        
        # Получаем vk_chat_id для этой группы
        vk_chats = db.get_group_vk_chats(group_id)
        if not vk_chats:
            print("❌ Нет связанных VK чатов для этой группы")
            return False
        
        vk_chat_id = vk_chats[0]['chat_id']
        print(f"📱 Используется VK чат: {vk_chat_id}")
        
        # Получаем сообщения за 15.10.2025
        messages = db.get_messages_by_date(vk_chat_id, "2025-10-15")
        
        if not messages:
            print("❌ Нет сообщений за 15.10.2025")
            return False
        
        print(f"📊 Найдено сообщений: {len(messages)}")
        
        # Создаем анализатор
        analyzer = ChatAnalyzer(AI_PROVIDERS)
        print(f"🔗 DEBUG: ChatAnalyzer создан")
        
        # Запускаем структурированный анализ
        print(f"🔄 Запуск структурированного анализа с {model_name}...")
        print("⏱️ Таймаут: 10 минут (600 секунд)")
        
        result = await analyzer.structured_analysis_with_specific_model(
            messages=messages,
            provider_name="ollama",
            model_name=model_name,
            user_id=None
        )
        
        if result:
            print("✅ Структурированный анализ завершен успешно!")
            print(f"📝 Сводка: {result.get('summary', '')[:100]}...")
            print(f"🔍 События: {len(result.get('events', []))}")
            print(f"🏷️ Классификация: {len(result.get('classification', []))}")
            
            # Проверяем создание логов
            import glob
            log_pattern = f"llm_logs/test_comparison/{model_name}/structured_analysis/*"
            log_files = glob.glob(log_pattern)
            
            if log_files:
                print(f"📁 Созданы логи: {len(log_files)} файлов")
                for log_file in sorted(log_files):
                    print(f"   📄 {log_file}")
                return True
            else:
                print("❌ Логи не созданы!")
                return False
        else:
            print("❌ Структурированный анализ не удался")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_all_models():
    """Тестируем логирование для всех доступных моделей"""
    print("🧪 Тестирование логирования для всех моделей")
    print("=" * 60)
    
    # Список моделей для тестирования
    models_to_test = [
        "deepseek-r1:8b",
        "gemma3:12b", 
        "gemma3:1b",
        "qwen3-coder:30b"
    ]
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n🔄 Тестирование модели: {model_name}")
        success = await test_logging_for_model(model_name)
        results[model_name] = success
        
        if success:
            print(f"✅ {model_name}: Логи созданы успешно")
        else:
            print(f"❌ {model_name}: Проблемы с логированием")
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 60)
    
    for model_name, success in results.items():
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"{model_name}: {status}")
    
    successful_models = sum(1 for success in results.values() if success)
    total_models = len(results)
    
    print(f"\n📈 Результат: {successful_models}/{total_models} моделей работают корректно")
    
    if successful_models == total_models:
        print("🎉 Все модели корректно создают логи!")
    else:
        print("⚠️ Есть проблемы с некоторыми моделями")

if __name__ == "__main__":
    asyncio.run(test_all_models())
