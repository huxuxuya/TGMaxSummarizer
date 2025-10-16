#!/usr/bin/env python3
"""
Тесты для проверки исправления проблем с telegramify-markdown
Особенно для случая из JSON лога с незакрытыми bold тегами
"""

import unittest
import logging
from telegram_message_sender import TelegramMessageSender
from telegram_formatter import TextContentType, TelegramFormatter
from telegram.constants import ParseMode

# Настройка логирования для тестов
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestTelegramifyFixes(unittest.TestCase):
    """Тесты для проверки исправления проблем с форматированием"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.sender = TelegramMessageSender()
    
    def test_problematic_case_from_json_log(self):
        """
        Тест для проблемного случая из JSON лога 2025-10-16-10-42-42-973448.json
        Проверяем что telegramify-markdown правильно обрабатывает списки с *
        """
        # Текст из JSON лога, который вызывал ошибку "can't find end of bold entity"
        # Конвертируем его в правильный стандартный Markdown
        problematic_text = """📊 **Анализ чата за 2025-10-15**

> 📈 **Статистика**
> • Сообщений: 62
> • Дата: 2025-10-15
> • Провайдер: Ollama (Локальная)
> • Модель: gemma3:27b
> • Режим: Стандартная (с рефлексией)

**📝 Первый ответ модели:**
> ## 📋 НОВАЯ ИНФОРМАЦИЯ:
> - Каникулы с 25 октября по 4 ноября.
> 
> ## 🚨 Родителям:
> - Домашнее задание: прописи страница 12 строчки 6,7,8.
> - Уточняется информация о работе кружков на каникулах.
> - Уточняется информация о 1 ноября (учатся ли дети).
> 
> ## ⚠️ Детям:
> - Выполнить домашнее задание: прописи страница 12 строчки 6,7,8.

**🤔 Результат рефлексии:**
> Анализ и советы по улучшению:
> 
> - **Неясно:** В разделе "Родителям" и "Детям" повторяется информация о домашнем задании. Можно объединить.
> - **Действия:** В разделе "Уточняется информация о работе кружков на каникулах" - неясно, что именно нужно уточнить - будут ли они работать, изменится ли расписание? Лучше сформулировать вопрос, например: "Уточняется, будут ли кружки работать во время каникул".
> - **Лишняя информация:** Нет лишней информации.
> - **Структура:** Можно объединить разделы "Родителям" и "Детям" в один, так как информация для них одинаковая. Например, "Домашнее задание: прописи страница 12 строчки 6,7,8".
> - Добавить: "Информация о 1 ноября (учатся ли дети) будет сообщено дополнительно".

**✨ Финальная суммаризация:**
> ## 📋 НОВАЯ ИНФОРМАЦИЯ:
> - Каникулы с 25 октября по 4 ноября.
> 
> ## 🚨 Родителям и детям:
> - Домашнее задание: прописи страница 12 строчки 6,7,8.
> - Уточняется, будут ли кружки работать во время каникул.
> - Информация о 1 ноября (учатся ли дети) будет сообщена дополнительно."""
        
        # Тестируем конвертацию через telegramify-markdown
        try:
            telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(problematic_text)
            
            # Проверяем что нет незакрытых тегов
            self._validate_telegram_markdown(telegram_text)
            
            logger.info("✅ Проблемный случай успешно обработан")
            logger.info(f"Результат: {telegram_text[:200]}...")
            
        except Exception as e:
            self.fail(f"Ошибка при конвертации проблемного текста: {e}")
    
    def test_list_markers_handling(self):
        """Тест обработки маркеров списков"""
        test_cases = [
            {
                "name": "Списки с * маркерами",
                "input": """## Анализ
*   **Пункт 1:** Описание первого пункта
*   **Пункт 2:** Описание второго пункта
*   **Пункт 3:** Описание третьего пункта""",
                "expected_contains": ["*", "Пункт 1", "Пункт 2", "Пункт 3"]
            },
            {
                "name": "Списки с - маркерами",
                "input": """## Список дел
- Первое дело
- Второе дело
- Третье дело""",
                "expected_contains": ["Первое дело", "Второе дело", "Третье дело"]
            },
            {
                "name": "Смешанные списки",
                "input": """## Смешанный список
*   **Важно:** Первый пункт
- Обычный пункт
*   **Критично:** Третий пункт""",
                "expected_contains": ["Важно", "Обычный пункт", "Критично"]
            }
        ]
        
        for case in test_cases:
            with self.subTest(case=case["name"]):
                try:
                    telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(case["input"])
                    
                    # Проверяем что результат содержит ожидаемые элементы
                    for expected in case["expected_contains"]:
                        self.assertIn(expected, telegram_text, 
                                    f"Ожидаемый элемент '{expected}' не найден в результате")
                    
                    # Проверяем валидность
                    self._validate_telegram_markdown(telegram_text)
                    
                    logger.info(f"✅ {case['name']} обработан успешно")
                    
                except Exception as e:
                    self.fail(f"Ошибка при обработке {case['name']}: {e}")
    
    def test_quote_blocks_handling(self):
        """Тест обработки блоков цитат"""
        test_text = """## Результат анализа

> **Важная информация:**
> - Первый пункт
> - Второй пункт
> 
> **Дополнительно:**
> Текст в цитате с **жирным** и *курсивом*."""
        
        try:
            telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(test_text)
            
            # Проверяем что цитаты обработаны правильно
            self.assertIn("Важная информация", telegram_text)
            self.assertIn("Первый пункт", telegram_text)
            self.assertIn("Дополнительно", telegram_text)
            
            # Проверяем валидность
            self._validate_telegram_markdown(telegram_text)
            
            logger.info("✅ Блоки цитат обработаны успешно")
            
        except Exception as e:
            self.fail(f"Ошибка при обработке блоков цитат: {e}")
    
    def test_nested_formatting(self):
        """Тест вложенного форматирования"""
        test_text = """## Сложное форматирование

**Заголовок раздела:**
- **Важный пункт:** Описание с *курсивом* и `кодом`
- Обычный пункт с [ссылкой](https://example.com)
- **Критичный пункт:** Текст с **жирным** и _подчеркиванием_

> **Цитата с форматированием:**
> - Пункт в цитате
> - Еще один пункт с **жирным** текстом"""
        
        try:
            telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(test_text)
            
            # Проверяем что форматирование сохранено
            self.assertIn("Заголовок раздела", telegram_text)
            self.assertIn("Важный пункт", telegram_text)
            self.assertIn("Критичный пункт", telegram_text)
            self.assertIn("Цитата с форматированием", telegram_text)
            
            # Проверяем валидность
            self._validate_telegram_markdown(telegram_text)
            
            logger.info("✅ Вложенное форматирование обработано успешно")
            
        except Exception as e:
            self.fail(f"Ошибка при обработке вложенного форматирования: {e}")
    
    def test_fallback_mechanism(self):
        """Тест механизма fallback при ошибках"""
        # Создаем текст, который может вызвать ошибку
        problematic_text = "Текст с проблемными символами: * [ ] ( ) ~ ` > # + - = | { } . !"
        
        try:
            # Это должно работать с fallback
            telegram_text = TelegramMessageSender.convert_standard_markdown_to_telegram(problematic_text)
            
            # Проверяем что результат не пустой
            self.assertIsNotNone(telegram_text)
            self.assertGreater(len(telegram_text), 0)
            
            logger.info("✅ Fallback механизм работает")
            
        except Exception as e:
            self.fail(f"Fallback механизм не сработал: {e}")
    
    def test_content_type_standard_markdown(self):
        """Тест использования TextContentType.STANDARD_MARKDOWN"""
        test_text = """## Тест стандартного Markdown

**Жирный текст** и *курсив*

- Список
- Элементы

[Ссылка](https://example.com)"""
        
        try:
            # Симулируем обработку через safe_send_message
            formatted_text = self._simulate_safe_send_message_processing(
                test_text, TextContentType.STANDARD_MARKDOWN
            )
            
            # Проверяем что текст обработан
            self.assertIsNotNone(formatted_text)
            self.assertGreater(len(formatted_text), 0)
            
            # Проверяем валидность
            self._validate_telegram_markdown(formatted_text)
            
            logger.info("✅ TextContentType.STANDARD_MARKDOWN работает")
            
        except Exception as e:
            self.fail(f"Ошибка при обработке TextContentType.STANDARD_MARKDOWN: {e}")
    
    def _convert_to_standard_markdown(self, text: str) -> str:
        """Конвертирует предварительно экранированный текст в стандартный Markdown"""
        # Убираем экранирование и конвертируем в стандартный Markdown
        import re
        
        # Заменяем экранированные символы
        text = text.replace('\\*', '*')
        text = text.replace('\\_', '_')
        text = text.replace('\\[', '[')
        text = text.replace('\\]', ']')
        text = text.replace('\\(', '(')
        text = text.replace('\\)', ')')
        text = text.replace('\\~', '~')
        text = text.replace('\\`', '`')
        text = text.replace('\\>', '>')
        text = text.replace('\\#', '#')
        text = text.replace('\\+', '+')
        text = text.replace('\\-', '-')
        text = text.replace('\\=', '=')
        text = text.replace('\\|', '|')
        text = text.replace('\\{', '{')
        text = text.replace('\\}', '}')
        text = text.replace('\\.', '.')
        text = text.replace('\\!', '!')
        
        # Конвертируем Telegram MarkdownV2 в стандартный Markdown
        # *text* -> **text** (bold)
        text = re.sub(r'\*([^*]+)\*', r'**\1**', text)
        
        # _text_ -> *text* (italic)
        text = re.sub(r'_([^_]+)_', r'*\1*', text)
        
        return text
    
    def _validate_telegram_markdown(self, text: str) -> None:
        """Валидирует Telegram MarkdownV2 текст"""
        # Проверяем на незакрытые теги
        asterisk_count = text.count('*')
        if asterisk_count % 2 != 0:
            self.fail(f"Несбалансированные bold теги: {asterisk_count} звездочек")
        
        underscore_count = text.count('_')
        if underscore_count % 2 != 0:
            self.fail(f"Несбалансированные italic теги: {underscore_count} подчеркиваний")
        
        backtick_count = text.count('`')
        if backtick_count % 2 != 0:
            self.fail(f"Несбалансированные code теги: {backtick_count} backticks")
    
    def _simulate_safe_send_message_processing(self, text: str, content_type: TextContentType) -> str:
        """Симулирует обработку текста в safe_send_message"""
        if content_type == TextContentType.STANDARD_MARKDOWN:
            return TelegramMessageSender.convert_standard_markdown_to_telegram(text)
        elif content_type == TextContentType.FORMATTED:
            return TelegramFormatter.smart_escape_markdown_v2(text)
        else:
            return text

if __name__ == '__main__':
    # Запуск тестов
    unittest.main(verbosity=2)
