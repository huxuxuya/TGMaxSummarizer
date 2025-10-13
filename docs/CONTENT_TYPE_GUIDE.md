# Руководство по использованию TextContentType

## Проблема

Раньше в боте происходило **двойное экранирование** специальных символов MarkdownV2:

```python
# ❌ СТАРЫЙ КОД (НЕПРАВИЛЬНО)
# handlers.py
safe_error_text = TelegramFormatter.escape_markdown_v2(str(e))  # Первое экранирование

# TelegramMessageSender.safe_edit_message_text()
markdown_text = TelegramFormatter.smart_escape_markdown_v2(text)  # Второе экранирование!

# Результат: parse_mode → parse\_mode → parse\\_mode ❌
```

## Решение

Введен `TextContentType` enum для явного указания типа контента и предотвращения двойного экранирования.

**Принцип:** Экранирование происходит ТОЛЬКО в `TelegramMessageSender`, никогда в handlers.

## Типы контента

### 1. TextContentType.RAW

**Когда использовать:** Обычный текст без форматирования (ошибки, статус, технические сообщения)

**Что делает:** Использует встроенный `telegram.helpers.escape_markdown(version=2)`

**Пример:**

```python
from telegram_formatter import TextContentType

await TelegramMessageSender.safe_edit_message_text(
    query,
    f"❌ Ошибка: {str(error)}",
    content_type=TextContentType.RAW  # Экранирует все спецсимволы
)

# Результат: ❌ Ошибка: Unsupported parse\_mode ✅
```

### 2. TextContentType.FORMATTED (по умолчанию)

**Когда использовать:** Текст с Markdown форматированием (`**bold**`, `_italic_`)

**Что делает:** Использует `TelegramFormatter.smart_escape_markdown_v2()`
- Конвертирует `**text**` → `*text*`
- НЕ экранирует `_` внутри слов (parse_mode остается parse_mode)
- Сохраняет курсив `_text_`

**Пример:**

```python
await TelegramMessageSender.safe_edit_message_text(
    query,
    result['display_text'],  # Содержит **жирный** и _курсив_
    content_type=TextContentType.FORMATTED  # Умное экранирование
)

# Результат: *жирный* и _курсив_ ✅
```

### 3. TextContentType.TECHNICAL

**Когда использовать:** Технический текст (имена переменных, методов, коды)

**Что делает:** Оборачивает текст в backticks \``text`\`

**Пример:**

```python
await TelegramMessageSender.safe_edit_message_text(
    query,
    f"Ошибка в методе: {method_name}",
    content_type=TextContentType.TECHNICAL
)

# Результат: Ошибка в методе: `parse_mode` ✅
```

## Миграция кода

### ❌ БЫЛО (неправильно):

```python
# handlers.py
safe_error_text = TelegramFormatter.escape_markdown_v2(str(e))

await TelegramMessageSender.safe_edit_message_text(
    query,
    f"❌ Ошибка: {safe_error_text}"
)
```

### ✅ СТАЛО (правильно):

```python
# handlers.py
from telegram_formatter import TextContentType

await TelegramMessageSender.safe_edit_message_text(
    query,
    f"❌ Ошибка: {str(e)}",
    content_type=TextContentType.RAW  # Экранирование автоматически
)
```

## Правила использования

1. **НЕ экранируйте текст вручную** перед вызовом `TelegramMessageSender`
2. **Всегда явно указывайте `content_type`** для ясности кода
3. **RAW** - для ошибок и обычного текста
4. **FORMATTED** - для суммаризаций и контента с форматированием
5. **TECHNICAL** - для имен переменных, методов, кодов

## Примеры

### Сообщения об ошибках

```python
await TelegramMessageSender.safe_edit_message_text(
    query,
    f"❌ Ошибка: {str(exception)}",
    content_type=TextContentType.RAW
)
```

### Суммаризация чата

```python
# В chat_analyzer.py результат уже содержит **жирный** текст
result = {
    'display_text': "*📝 Важно:* конкурс **завтра**"
}

# В handlers.py
await TelegramMessageSender.safe_edit_message_text(
    query,
    result['display_text'],
    content_type=TextContentType.FORMATTED  # По умолчанию
)
```

### Технические детали

```python
await TelegramMessageSender.safe_edit_message_text(
    query,
    f"Метод {method_name} завершился с ошибкой",
    content_type=TextContentType.TECHNICAL
)
```

## Преимущества нового подхода

1. ✅ **Нет двойного экранирования** - проблема решена
2. ✅ **Явность** - четко видно, какой тип контента
3. ✅ **Единая точка экранирования** - только в TelegramMessageSender
4. ✅ **Использование стандартов** - telegram.helpers для RAW
5. ✅ **Обратная совместимость** - по умолчанию FORMATTED
6. ✅ **Легко тестировать** - простая логика if/elif

## Отладка

Если возникают проблемы с форматированием:

1. Проверьте, что НЕ экранируете текст вручную
2. Убедитесь, что указан правильный `content_type`
3. Проверьте логи - они показывают какой метод используется:

```
DEBUG: Content type: TextContentType.RAW
DEBUG: Using telegram.helpers.escape_markdown() for RAW content
```

## FAQ

**Q: Какой content_type использовать по умолчанию?**  
A: `TextContentType.FORMATTED` - он установлен по умолчанию для обратной совместимости.

**Q: Нужно ли экранировать текст перед вызовом TelegramMessageSender?**  
A: НЕТ! Никогда не экранируйте текст вручную. Экранирование произойдет автоматически.

**Q: Что делать, если в тексте есть переменные с символами _ ?**  
A: Используйте `TextContentType.RAW` - он правильно экранирует все символы.

**Q: Можно ли смешивать форматирование и технический текст?**  
A: Да, используйте `TextContentType.FORMATTED` и вставляйте технические термины в backticks вручную.

