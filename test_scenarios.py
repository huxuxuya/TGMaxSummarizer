#!/usr/bin/env python3
"""
Тестовый скрипт для сравнения сценариев суммаризации
"""
import os

# Устанавливаем переменные окружения ДО всех импортов!
os.environ['OLLAMA_BASE_URL'] = 'http://192.168.1.75:11434'
print(f"🔗 DEBUG: Устанавливаем OLLAMA_BASE_URL = {os.environ['OLLAMA_BASE_URL']}")

import asyncio
import logging
import time
import aiohttp
import json
import sys
import select
import tty
import termios
from database import DatabaseManager
from chat_analyzer import ChatAnalyzer

class ProgressChatAnalyzer(ChatAnalyzer):
    """
    Обертка над ChatAnalyzer для показа прогресса генерации
    """
    def __init__(self, config, show_generation=False, animation_speed=0.02):
        super().__init__(config)
        self.show_generation = show_generation
        self.animation_speed = animation_speed
    
    async def analyze_chat_with_specific_model(self, messages, provider_name, model_id, user_id=None, 
                                             enable_reflection=False, clean_data_first=False):
        """
        Анализ чата с показом прогресса
        """
        if not self.show_generation:
            return await super().analyze_chat_with_specific_model(
                messages, provider_name, model_id, user_id, enable_reflection, clean_data_first
            )
        
        print_progress_stage("📊 Анализ чата", f"Модель: {model_id}")
        
        # Создаем LLM логгер для тестового режима
        from llm_logger import LLMLogger
        import os
        
        # Определяем сценарий
        if clean_data_first:
            scenario = "with_cleaning"
        elif enable_reflection:
            scenario = "with_reflection"
        else:
            scenario = "without_reflection"
        
        # Проверяем, есть ли в окружении флаг тестового режима
        test_mode = os.environ.get('TEST_MODE') == 'true'
        
        # Создаем логгер
        llm_logger = LLMLogger(
            scenario=scenario,
            model_name=model_id,
            test_mode=test_mode
        )
        llm_logger.set_session_info(provider_name, model_id, None, user_id)
        
        # Получаем провайдер
        if provider_name == 'ollama' and 'ollama' in self.config:
            provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
        else:
            provider = self.provider_factory.create_provider(provider_name, self.config)
        if not provider:
            print("❌ Провайдер не найден")
            return None
        
        # Устанавливаем модель
        if hasattr(provider, 'set_model'):
            provider.set_model(model_id)
        
        # Очистка данных
        if clean_data_first:
            print_progress_stage("🧹 Очистка данных", "Фильтрация сообщений...")
            
            # Создаем временный контекст для очистки
            temp_chat_context = {
                'total_messages': len(messages),
                'date': messages[0].get('message_time', 0) if messages else 0,
                'provider': provider_name,
                'model': model_id
            }
            
            messages = await self.clean_messages(provider, messages, temp_chat_context, llm_logger)
            if not messages:
                print("❌ Очистка данных не удалась или не осталось сообщений")
                return None
            print(f"✅ Очищено сообщений: {len(messages)}")
        
        # Суммаризация
        print_progress_stage("📝 Суммаризация", "Генерация основного резюме...")
        summary = await provider.summarize_chat(messages)
        
        if self.show_generation and summary:
            print_with_animation(summary, "📝 Суммаризация", self.animation_speed)
        
        # Логируем результат
        if llm_logger and summary:
            llm_logger.log_raw_result(summary)
            llm_logger.log_formatted_result(summary)
            llm_logger.log_session_summary({
                'summary': summary,
                'messages_count': len(messages),
                'model': model_id,
                'provider': provider_name
            })
        
        if not enable_reflection:
            return summary
        
        # Рефлексия
        print_progress_stage("🤔 Рефлексия", "Анализ качества суммаризации...")
        reflection = await provider.generate_response(
            f"Проанализируй качество этой суммаризации и предложи улучшения:\n\n{summary}"
        )
        
        if self.show_generation and reflection:
            print_with_animation(reflection, "🤔 Рефлексия", self.animation_speed)
        
        # Улучшение
        print_progress_stage("✨ Улучшение", "Генерация улучшенной версии...")
        improved = await provider.generate_response(
            f"Улучши эту суммаризацию на основе анализа:\n\nСуммаризация:\n{summary}\n\nАнализ:\n{reflection}"
        )
        
        if self.show_generation and improved:
            print_with_animation(improved, "✨ Улучшение", self.animation_speed)
        
        return {
            'summary': summary,
            'reflection': reflection,
            'improved': improved
        }
    
    async def structured_analysis_with_specific_model(self, messages, provider_name, model_name, user_id):
        """
        Структурированный анализ с показом прогресса
        """
        if not self.show_generation:
            return await super().structured_analysis_with_specific_model(
                messages, provider_name, model_name, user_id
            )
        
        print_progress_stage("🏗️ Структурированный анализ", f"Модель: {model_name}")
        
        # Создаем LLM Logger для логирования
        import os
        from llm_logger import LLMLogger
        
        test_mode = os.environ.get('TEST_MODE') == 'true'
        llm_logger = LLMLogger(
            scenario="structured_analysis",
            model_name=model_name,
            test_mode=test_mode
        )
        
        # Устанавливаем метаданные сессии
        llm_logger.set_session_info(provider_name, model_name, None, user_id)
        
        # Получаем провайдер
        if provider_name == 'ollama' and 'ollama' in self.config:
            provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
        else:
            provider = self.provider_factory.create_provider(provider_name, self.config)
        if not provider:
            print("❌ Провайдер не найден")
            return None
        
        # Устанавливаем модель
        if hasattr(provider, 'set_model'):
            provider.set_model(model_name)
        
        # Классификация
        print_progress_stage("🏷️ Классификация", "Анализ типов сообщений...")
        
        # Создаем callback для потоковой генерации
        def classification_callback(chunk):
            if self.show_generation:
                print(chunk, end='', flush=True)
        
        classification = await self._classify_messages(provider, messages, llm_logger, stream_callback=classification_callback)
        
        if self.show_generation and classification:
            print()  # Новая строка после анимации
        
        # Фильтрация релевантных сообщений - используем встроенный метод
        relevant_messages = self._filter_by_classification(messages, classification)
        
        print(f"✅ Отфильтровано релевантных сообщений: {len(relevant_messages)} из {len(messages)}")
        
        # Экстракция слотов
        print_progress_stage("🔍 Экстракция слотов", "Извлечение событий и фактов...")
        
        def extraction_callback(chunk):
            if self.show_generation:
                print(chunk, end='', flush=True)
        
        events = await self._extract_slots(provider, relevant_messages, classification, llm_logger, stream_callback=extraction_callback)
        
        if self.show_generation and events:
            print()  # Новая строка после анимации
        
        # Генерация сводки для родителей
        print_progress_stage("👨‍👩‍👧‍👦 Сводка для родителей", "Создание итогового отчета...")
        
        def summary_callback(chunk):
            if self.show_generation:
                print(chunk, end='', flush=True)
        
        summary = await self._generate_parent_summary(provider, events, llm_logger, stream_callback=summary_callback)
        
        if self.show_generation and summary:
            print()  # Новая строка после анимации
        
        # Логируем финальные результаты
        if llm_logger and summary:
            llm_logger.log_raw_result(summary)
            llm_logger.log_formatted_result(summary)
            llm_logger.log_session_summary({
                'summary': summary,
                'events': events,
                'classification': classification
            })
        
        return {
            'summary': summary,
            'events': events,
            'classification': classification
        }

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

def print_with_animation(text: str, prefix: str = "🤖", delay: float = 0.02):
    """
    Выводить текст с анимацией печати
    """
    print(f"\n{prefix} Генерация:")
    print("-" * 50)
    
    # Мгновенный режим
    if delay == 0:
        print(text)
        print("-" * 50)
        return
    
    print("💡 Нажмите любую клавишу для ускорения анимации")
    print("-" * 50)
    
    # Проверяем, не слишком ли длинный текст для анимации
    if len(text) > 1000 and delay > 0.01:
        print("⚠️ Длинный текст, ускоряем анимацию...")
        delay = min(delay, 0.01)
    
    for i, char in enumerate(text):
        print(char, end='', flush=True)
        
        # Проверяем нажатие клавиши каждые 10 символов
        if i % 10 == 0 and check_key_pressed():
            key = get_key()
            if key:
                print(f"\n⚡ Анимация ускорена! (нажата клавиша: {repr(key)})")
                delay = 0.001  # Ускоряем анимацию
        
        time.sleep(delay)
    
    print("\n" + "-" * 50)

def print_progress_stage(stage: str, description: str = ""):
    """
    Выводить информацию о текущем этапе
    """
    print(f"\n🔄 {stage}")
    if description:
        print(f"   {description}")
    print("-" * 30)

def check_key_pressed():
    """
    Проверить, нажата ли клавиша (неблокирующая проверка)
    """
    try:
        if sys.platform == 'win32':
            import msvcrt
            return msvcrt.kbhit()
        else:
            return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    except:
        return False

def get_key():
    """
    Получить нажатую клавишу
    """
    try:
        if sys.platform == 'win32':
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:
            return sys.stdin.read(1)
    except:
        return None

async def get_available_models(base_url: str) -> list:
    """
    Получить список доступных моделей с сервера Ollama
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/api/tags", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model_info in data.get('models', []):
                        model_name = model_info.get('name', '')
                        if model_name:
                            models.append(model_name)
                    return models
                else:
                    print(f"❌ Ошибка получения моделей: HTTP {response.status}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка подключения к Ollama: {e}")
        return []

async def main():
    print("🤖 Тестирование сценариев суммаризации")
    print("✨ Возможности:")
    print("   • Показ генерируемого текста в реальном времени (включен по умолчанию)")
    print("   • Максимально быстрый вывод без задержек")
    print("   • Потоковая генерация от Ollama API")
    print("   • Подробный прогресс по этапам\n")
    
    # 1. Получение списка доступных моделей с сервера Ollama
    base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    print(f"🔍 Получаем список моделей с сервера {base_url}...")
    
    available_models = await get_available_models(base_url)
    
    if not available_models:
        print("❌ Не удалось получить список моделей или сервер недоступен")
        print("💡 Убедитесь, что Ollama запущен и доступен по адресу:", base_url)
        return
    
    # Создаем словарь для выбора моделей
    models = {}
    for i, model in enumerate(available_models, 1):
        models[str(i)] = model
    
    print(f"\n✅ Найдено {len(available_models)} моделей:")
    for key, model in models.items():
        print(f"  {key}. {model}")
    
    choice = input(f"\nВыберите модель (1-{len(available_models)}): ").strip()
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
    
    # 2.5. Настройка отображения (включено по умолчанию)
    show_generation = True  # Всегда включено
    animation_speed = 0.02  # Нормальная скорость
    
    print("✅ Показ генерируемого текста включен по умолчанию")
    print(f"✅ Скорость анимации: {animation_speed}s на символ (нормально)")
    
    print()
    
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
        messages = db.get_messages_by_date(vk_chat_id, "2025-10-16")
        
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
    
    print(f"🔗 DEBUG: Переменная окружения OLLAMA_BASE_URL = {os.environ.get('OLLAMA_BASE_URL')}")
    
    # 5. Создаем анализатор с явной конфигурацией
    try:
        # Передаем конфигурацию явно, чтобы использовать обновленные переменные окружения
        from config import AI_PROVIDERS
        analyzer = ProgressChatAnalyzer(AI_PROVIDERS, show_generation=show_generation, animation_speed=animation_speed)
        print(f"🔗 DEBUG: ProgressChatAnalyzer создан с конфигурацией: {analyzer.config.get('ollama', {}).get('base_url', 'НЕ НАЙДЕНО')}")
        print(f"🔗 DEBUG: Показ генерации: {'включен' if show_generation else 'отключен'}")
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
    
    if scenario_choice == '5':
        print("\nВсе сценарии:")
        print("  1. 1_without_reflection/ - быстрая суммаризация")
        print("  2. 2_with_reflection/ - с рефлексией и улучшением")
        print("  3. 3_with_cleaning/ - с предварительной очисткой")
        print("  4. 4_structured_analysis/ - структурированный анализ")
    else:
        # Показываем только запущенный сценарий
        scenario_info = {
            '1': ("1_without_reflection", "быстрая суммаризация"),
            '2': ("2_with_reflection", "с рефлексией и улучшением"),
            '3': ("3_with_cleaning", "с предварительной очисткой"),
            '4': ("4_structured_analysis", "структурированный анализ")
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
