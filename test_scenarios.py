#!/usr/bin/env python3
"""
Тестовый скрипт для сравнения сценариев суммаризации
"""
import os
import asyncio
import logging
import time
from database import DatabaseManager
from chat_analyzer import ChatAnalyzer

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def estimate_tokens(text: str) -> int:
    """
    Примерная оценка количества токенов в тексте
    (примерно 4 символа = 1 токен для русского текста)
    """
    return len(text) // 4

def calculate_tokens_per_second(response_text: str, duration: float) -> float:
    """
    Вычислить количество токенов в секунду
    """
    if duration <= 0:
        return 0.0
    
    tokens = estimate_tokens(response_text)
    return tokens / duration

def format_duration(seconds: float) -> str:
    """
    Форматировать время в читаемый вид
    """
    if seconds < 60:
        return f"{seconds:.1f}с"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}м {secs:.1f}с"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}ч {minutes}м {secs:.1f}с"

async def main():
    print("🤖 Тестирование сценариев суммаризации\n")
    
    # 1. Выбор модели
    models = {
        '1': 'deepseek-r1:8b',
        '2': 'gemma3:12b',
        '3': 'qwen3:8b'
    }
    
    print("Доступные модели Ollama:")
    for key, model in models.items():
        print(f"  {key}. {model}")
    
    choice = input("\nВыберите модель (1-3): ").strip()
    model_name = models.get(choice)
    
    if not model_name:
        print("❌ Неверный выбор")
        return
    
    print(f"\n✅ Выбрана модель: {model_name}\n")
    
    # 2. Выбор сценария
    print("Доступные сценарии:")
    print("  1. Без рефлексии (быстрая суммаризация)")
    print("  2. С рефлексией (анализ и улучшение)")
    print("  3. С предварительной очисткой (фильтрация + рефлексия)")
    print("  4. Структурированный анализ (классификация + экстракция + сводка)")
    print("  5. Все сценарии (сравнение)")
    
    scenario_choice = input("\nВыберите сценарий (1-5): ").strip()
    
    if scenario_choice not in ['1', '2', '3', '4', '5']:
        print("❌ Неверный выбор сценария")
        return
    
    print(f"\n✅ Выбран сценарий: {scenario_choice}\n")
    
    # 3. Получение данных из БД
    try:
        db = DatabaseManager('bot_database.db')
        
        # Получаем все группы из базы данных
        all_groups = db.get_all_groups()
        
        if not all_groups:
            print("❌ Нет групп в базе данных")
            return
        
        # Берем первую группу
        chat_info = all_groups[0]
        group_id = chat_info['group_id']
        chat_name = chat_info.get('group_name', 'Unknown')
        
        print(f"📱 Используется группа: {chat_name} (ID: {group_id})")
        
        # Получаем vk_chat_id для этой группы
        vk_chats = db.get_group_vk_chats(group_id)
        if not vk_chats:
            print("❌ Нет связанных VK чатов для этой группы")
            return
        
        vk_chat_id = vk_chats[0]['chat_id']
        print(f"📱 Используется VK чат: {vk_chat_id}")
        
        # Получаем сообщения за 13.10.2025
        messages = db.get_messages_by_date(vk_chat_id, "2025-10-13")
        
        if not messages:
            print("❌ Нет сообщений за 13.10.2025")
            return
        
        print(f"📊 Найдено сообщений: {len(messages)}\n")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с базой данных: {e}")
        return
    
    # 4. Устанавливаем переменные окружения для тестового режима
    os.environ['TEST_MODE'] = 'true'
    os.environ['TEST_MODEL_NAME'] = model_name
    os.environ['ENABLE_LLM_LOGGING'] = 'true'
    
    # 5. Создаем анализатор
    try:
        analyzer = ChatAnalyzer()  # Используем конфигурацию по умолчанию
    except Exception as e:
        print(f"❌ Ошибка при создании анализатора: {e}")
        return
    
    # 6. Определяем сценарии для запуска
    all_scenarios = [
        ("1_without_reflection", False, False, False, "Без рефлексии"),
        ("2_with_reflection", True, False, False, "С рефлексией"),
        ("3_with_cleaning", True, True, False, "С предварительной очисткой"),
        ("4_structured_analysis", False, False, True, "Структурированный анализ")
    ]
    
    # Выбираем сценарии в зависимости от выбора пользователя
    if scenario_choice == '1':
        scenarios_to_run = [all_scenarios[0]]
    elif scenario_choice == '2':
        scenarios_to_run = [all_scenarios[1]]
    elif scenario_choice == '3':
        scenarios_to_run = [all_scenarios[2]]
    elif scenario_choice == '4':
        scenarios_to_run = [all_scenarios[3]]
    else:  # scenario_choice == '5'
        scenarios_to_run = all_scenarios
    
    results = {}
    
    # 7. Запускаем выбранные сценарии
    performance_stats = {}
    
    for scenario_name, enable_reflection, clean_data_first, structured_analysis, description in scenarios_to_run:
        print(f"🔄 Запуск сценария: {description} ({scenario_name})...")
        
        start_time = time.time()
        
        try:
            if structured_analysis:
                # Структурированный анализ
                result = await analyzer.structured_analysis_with_specific_model(
                    messages=messages,
                    provider_name="ollama",
                    model_name=model_name,
                    user_id=None
                )
            else:
                # Обычный анализ
                result = await analyzer.analyze_chat_with_specific_model(
                    messages=messages,
                    provider_name="ollama",
                    model_id=model_name,
                    user_id=None,
                    enable_reflection=enable_reflection,
                    clean_data_first=clean_data_first
                )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if result:
                # Анализируем результат для подсчета токенов
                if isinstance(result, dict):
                    if structured_analysis:
                        # Структурированный анализ
                        summary_text = result.get('summary', '') or ''
                        events = result.get('events', [])
                        classification = result.get('classification', [])
                        
                        # Подсчитываем токены для всех компонентов
                        events_text = str(events) if events else ''
                        classification_text = str(classification) if classification else ''
                        
                        total_tokens = estimate_tokens(summary_text) + estimate_tokens(events_text) + estimate_tokens(classification_text)
                        tokens_per_sec = calculate_tokens_per_second(summary_text + events_text + classification_text, duration)
                    else:
                        # Обычный анализ с рефлексией
                        summary_text = result.get('summary', '') or ''
                        reflection_text = result.get('reflection', '') or ''
                        improved_text = result.get('improved', '') or ''
                        
                        total_tokens = estimate_tokens(summary_text) + estimate_tokens(reflection_text) + estimate_tokens(improved_text)
                        tokens_per_sec = calculate_tokens_per_second(summary_text + reflection_text + improved_text, duration)
                else:
                    # Если результат - строка (без рефлексии)
                    result_text = str(result) if result else ''
                    total_tokens = estimate_tokens(result_text)
                    tokens_per_sec = calculate_tokens_per_second(result_text, duration)
                
                performance_stats[scenario_name] = {
                    'duration': duration,
                    'tokens': total_tokens,
                    'tokens_per_sec': tokens_per_sec,
                    'success': True
                }
                
                print(f"✅ Сценарий {description} завершен")
                print(f"⏱️  Время выполнения: {format_duration(duration)}")
                print(f"🔢 Токенов сгенерировано: ~{total_tokens}")
                print(f"🚀 Скорость: {tokens_per_sec:.1f} токенов/сек")
                results[scenario_name] = "Успешно"
            else:
                end_time = time.time()
                duration = end_time - start_time
                performance_stats[scenario_name] = {
                    'duration': duration,
                    'tokens': 0,
                    'tokens_per_sec': 0.0,
                    'success': False
                }
                print(f"❌ Ошибка в сценарии {description}")
                print(f"⏱️  Время до ошибки: {format_duration(duration)}")
                results[scenario_name] = "Ошибка"
                
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            performance_stats[scenario_name] = {
                'duration': duration,
                'tokens': 0,
                'tokens_per_sec': 0.0,
                'success': False
            }
            print(f"❌ Исключение в сценарии {description}: {e}")
            print(f"⏱️  Время до ошибки: {format_duration(duration)}")
            results[scenario_name] = f"Исключение: {e}"
        
        print()
    
    # 8. Вывод результатов
    print("\n" + "="*60)
    print("✅ Тестирование завершено!")
    print(f"📁 Результаты: llm_logs/test_comparison/{model_name}/")
    
    if scenario_choice == '4':
        print("\nВсе сценарии:")
        print("  1. 1_without_reflection/ - быстрая суммаризация")
        print("  2. 2_with_reflection/ - с рефлексией и улучшением")
        print("  3. 3_with_cleaning/ - с предварительной очисткой")
    else:
        # Показываем только запущенный сценарий
        scenario_info = {
            '1': ("1_without_reflection", "быстрая суммаризация"),
            '2': ("2_with_reflection", "с рефлексией и улучшением"),
            '3': ("3_with_cleaning", "с предварительной очисткой")
        }
        scenario_name, description = scenario_info[scenario_choice]
        print(f"\nЗапущенный сценарий:")
        print(f"  {scenario_name}/ - {description}")
    
    print("\nСтатус выполнения:")
    for scenario, status in results.items():
        print(f"  {scenario}: {status}")
    
    # Выводим статистику производительности
    if performance_stats:
        print("\n📊 Статистика производительности:")
        print("-" * 60)
        
        for scenario_name, stats in performance_stats.items():
            if stats['success']:
                print(f"  {scenario_name}:")
                print(f"    ⏱️  Время: {format_duration(stats['duration'])}")
                print(f"    🔢 Токенов: ~{stats['tokens']}")
                print(f"    🚀 Скорость: {stats['tokens_per_sec']:.1f} токенов/сек")
            else:
                print(f"  {scenario_name}: ❌ Не удалось измерить (ошибка)")
        
        # Сравнительная статистика
        if len(performance_stats) > 1:
            successful_stats = {k: v for k, v in performance_stats.items() if v['success']}
            if successful_stats:
                print("\n🏆 Сравнение сценариев:")
                fastest = max(successful_stats.items(), key=lambda x: x[1]['tokens_per_sec'])
                slowest = min(successful_stats.items(), key=lambda x: x[1]['tokens_per_sec'])
                
                print(f"  🥇 Самый быстрый: {fastest[0]} ({fastest[1]['tokens_per_sec']:.1f} токенов/сек)")
                print(f"  🐌 Самый медленный: {slowest[0]} ({slowest[1]['tokens_per_sec']:.1f} токенов/сек)")
                
                # Общая статистика
                total_duration = sum(s['duration'] for s in successful_stats.values())
                total_tokens = sum(s['tokens'] for s in successful_stats.values())
                avg_speed = total_tokens / total_duration if total_duration > 0 else 0
                
                print(f"  📈 Общая производительность:")
                print(f"    ⏱️  Общее время: {format_duration(total_duration)}")
                print(f"    🔢 Общее токенов: ~{total_tokens}")
                print(f"    🚀 Средняя скорость: {avg_speed:.1f} токенов/сек")
    
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
