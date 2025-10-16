#!/usr/bin/env python3
"""
Пример использования telegramify-markdown в проекте TGMaxSummarizer
"""

import asyncio
import logging
from telegram_message_sender import TelegramMessageSender
from telegram_formatter import TextContentType
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def example_usage():
    """
    Демонстрирует различные способы использования telegramify-markdown
    """
    
    # Пример 1: Стандартный Markdown
    standard_markdown = """
# Заголовок документа

Это **жирный текст** и *курсив*.

## Список покупок
- Молоко
- Хлеб
- Яйца

### Код
```python
def hello():
    print("Hello, World!")
```

[Ссылка на GitHub](https://github.com)
"""
    
    print("=== ПРИМЕР 1: Стандартный Markdown ===")
    print("Исходный текст:")
    print(standard_markdown)
    print("\nКонвертированный в Telegram MarkdownV2:")
    telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(standard_markdown)
    print(telegram_text)
    print("\n" + "="*50 + "\n")
    
    # Пример 2: HTML контент
    html_content = """
<h1>Отчет о работе</h1>
<p>Сегодня мы <strong>успешно</strong> завершили проект.</p>
<p>Основные <em>достижения</em>:</p>
<ul>
    <li>Реализована новая функция</li>
    <li>Исправлены баги</li>
    <li>Добавлены тесты</li>
</ul>
<p>Код функции:</p>
<pre><code>def process_data(data):
    return data.upper()</code></pre>
<p>Подробнее: <a href="https://example.com">здесь</a></p>
"""
    
    print("=== ПРИМЕР 2: HTML контент ===")
    print("Исходный HTML:")
    print(html_content)
    print("\nКонвертированный в Telegram MarkdownV2:")
    telegram_html = TelegramMessageSender.convert_html_to_telegram_markdown(html_content)
    print(telegram_html)
    print("\n" + "="*50 + "\n")
    
    # Пример 3: Использование в safe_send_message (симуляция)
    print("=== ПРИМЕР 3: Использование в safe_send_message ===")
    
    # Симулируем отправку сообщения с разными типами контента
    test_cases = [
        {
            "name": "Стандартный Markdown",
            "text": "## Результат анализа\n\n**Статус**: ✅ Успешно\n\n*Время выполнения*: 2.5 секунды",
            "content_type": TextContentType.STANDARD_MARKDOWN
        },
        {
            "name": "HTML контент",
            "text": "<h2>Сводка</h2><p><b>Обработано</b>: 150 сообщений</p><p><i>Ошибок</i>: 0</p>",
            "content_type": TextContentType.HTML
        },
        {
            "name": "Форматированный текст",
            "text": "**Важно**: Проверьте настройки\\!",
            "content_type": TextContentType.FORMATTED
        },
        {
            "name": "Технический текст",
            "text": "ERROR: Connection timeout after 30 seconds",
            "content_type": TextContentType.TECHNICAL
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"Тест {i}: {case['name']}")
        print(f"Исходный текст: {case['text']}")
        
        # Симулируем обработку текста
        if case['content_type'] == TextContentType.STANDARD_MARKDOWN:
            processed_text = TelegramMessageSender.convert_standard_markdown_to_telegram(case['text'])
        elif case['content_type'] == TextContentType.HTML:
            processed_text = TelegramMessageSender.convert_html_to_telegram_markdown(case['text'])
        elif case['content_type'] == TextContentType.FORMATTED:
            from telegram_formatter import TelegramFormatter
            processed_text = TelegramFormatter.smart_escape_markdown_v2(case['text'])
        elif case['content_type'] == TextContentType.TECHNICAL:
            processed_text = f"`{case['text']}`"
        else:
            processed_text = case['text']
        
        print(f"Обработанный текст: {processed_text}")
        print("-" * 30)

def demonstrate_telegramify_features():
    """
    Демонстрирует возможности telegramify-markdown
    """
    import telegramify_markdown
    
    print("=== ДЕМОНСТРАЦИЯ ВОЗМОЖНОСТЕЙ TELEGRAMIFY-MARKDOWN ===")
    
    # Сложный Markdown с различными элементами
    complex_markdown = """
# 📊 Анализ данных

## 📈 Статистика
- **Всего сообщений**: 1,234
- **Уникальных пользователей**: 567
- **Средняя длина**: 45 символов

### 🔍 Детали
| Метрика | Значение | Изменение |
|---------|----------|-----------|
| Активность | 89% | ↗️ +5% |
| Время ответа | 1.2с | ↘️ -0.3с |

### 💻 Код обработки
```python
def analyze_messages(messages):
    total = len(messages)
    unique_users = len(set(msg.user_id for msg in messages))
    avg_length = sum(len(msg.text) for msg in messages) / total
    return {
        'total': total,
        'unique_users': unique_users,
        'avg_length': avg_length
    }
```

### 📝 Примечания
> **Важно**: Данные обновляются каждые 5 минут

[Подробный отчет](https://analytics.example.com/report)
"""
    
    print("Исходный Markdown:")
    print(complex_markdown)
    print("\n" + "="*50)
    print("Конвертированный через telegramify-markdown:")
    
    try:
        telegram_result = telegramify_markdown.markdownify(complex_markdown)
        print(telegram_result)
    except Exception as e:
        print(f"Ошибка конвертации: {e}")
        print("Используем fallback метод...")
        telegram_result = TelegramMessageSender.convert_standard_markdown_to_telegram(complex_markdown)
        print(telegram_result)

if __name__ == "__main__":
    print("🚀 Запуск примеров использования telegramify-markdown\n")
    
    # Демонстрация возможностей
    demonstrate_telegramify_features()
    
    print("\n" + "="*60 + "\n")
    
    # Примеры использования
    asyncio.run(example_usage())
    
    print("\n✅ Все примеры выполнены успешно!")
    print("\n📋 Инструкции по использованию:")
    print("1. Установите зависимость: pip install telegramify-markdown")
    print("2. Используйте TextContentType.STANDARD_MARKDOWN для стандартного Markdown")
    print("3. Используйте TextContentType.HTML для HTML контента")
    print("4. Библиотека автоматически обработает fallback при ошибках")
