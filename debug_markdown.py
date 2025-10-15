#!/usr/bin/env python3
"""
Скрипт для отладки проблем с форматированием MarkdownV2
"""
import asyncio
import logging
from telegram_formatter import TelegramFormatter, TextContentType
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_markdown_formatting():
    """Тестируем различные сценарии форматирования"""
    
    print("🧪 Тестирование форматирования MarkdownV2")
    print("=" * 60)
    
    # Тестовые случаи
    test_cases = [
        {
            "name": "Простой текст",
            "text": "Привет, мир!",
            "content_type": TextContentType.RAW
        },
        {
            "name": "Текст с символом #",
            "text": "Ошибка анализа: Can't parse entities: character '#' is reserved",
            "content_type": TextContentType.RAW
        },
        {
            "name": "Текст с жирным шрифтом",
            "text": "Это *жирный* текст",
            "content_type": TextContentType.FORMATTED
        },
        {
            "name": "Несбалансированные теги",
            "text": "Это *жирный текст без закрытия",
            "content_type": TextContentType.FORMATTED
        },
        {
            "name": "Сложный текст с разными символами",
            "text": "Тест: [ссылка](url), *жирный*, _курсив_, `код`, # заголовок",
            "content_type": TextContentType.FORMATTED
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}:")
        print(f"   Исходный текст: {test_case['text']}")
        print(f"   Content type: {test_case['content_type']}")
        
        try:
            if test_case['content_type'] == TextContentType.RAW:
                formatted = escape_markdown(test_case['text'], version=2)
                print(f"   Метод: telegram.helpers.escape_markdown()")
            else:
                formatted = TelegramFormatter.smart_escape_markdown_v2(test_case['text'])
                print(f"   Метод: TelegramFormatter.smart_escape_markdown_v2()")
            
            print(f"   Результат: {formatted}")
            
            # Проверяем баланс тегов
            asterisk_count = formatted.count('*')
            if asterisk_count % 2 != 0:
                print(f"   ⚠️ ПРОБЛЕМА: Несбалансированные теги жирного шрифта ({asterisk_count} звездочек)")
            else:
                print(f"   ✅ OK: Сбалансированные теги ({asterisk_count} звездочек)")
                
        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")

def analyze_problematic_text():
    """Анализируем проблемный текст из логов"""
    
    print("\n🔍 Анализ проблемного текста из логов")
    print("=" * 60)
    
    # Текст из лога
    problematic_text = "❌ Ошибка анализа: Can't parse entities: character '#' is reserved and must be escaped with the preceding '\\'"
    
    print(f"Проблемный текст: {problematic_text}")
    
    # Тестируем разные методы экранирования
    methods = [
        ("telegram.helpers.escape_markdown", lambda t: escape_markdown(t, version=2)),
        ("TelegramFormatter.smart_escape_markdown_v2", lambda t: TelegramFormatter.smart_escape_markdown_v2(t))
    ]
    
    for method_name, method_func in methods:
        print(f"\n📝 Метод: {method_name}")
        try:
            result = method_func(problematic_text)
            print(f"   Результат: {result}")
            
            # Анализируем символы
            chars_to_check = ['*', '_', '#', '\\']
            for char in chars_to_check:
                count = result.count(char)
                if count > 0:
                    print(f"   Символ '{char}': {count} раз")
                    
        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")

if __name__ == "__main__":
    test_markdown_formatting()
    analyze_problematic_text()
    
    print("\n" + "=" * 60)
    print("📋 Рекомендации для отладки:")
    print("1. Запустите бота с этим скриптом")
    print("2. Воспроизведите ошибку")
    print("3. Проверьте логи на наличие 'UNBALANCED BOLD TAGS' или других предупреждений")
    print("4. Найдите текст, который вызывает ошибку")
    print("5. Используйте этот скрипт для тестирования проблемного текста")
