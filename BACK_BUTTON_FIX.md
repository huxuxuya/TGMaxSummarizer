# 🔧 ИСПРАВЛЕНИЕ: Кнопка "Назад" из просмотра суммаризации

## ❌ Проблема
Кнопка "Назад" из просмотра суммаризации не работала.

## 🔍 Причина
Проблема была в **неправильном парсинге `vk_chat_id`** в обработчиках.

### Проблемный код:
```python
vk_chat_id = query.data.split('_')[-1]
```

### Проблема:
Если `vk_chat_id` содержит подчеркивания (например `123_456`), то:
- `callback_data = "quick_chat_123_456"`
- `split('_')[-1]` вернет только `"456"` вместо `"123_456"`

## ✅ Решение
Заменил все проблемные места на правильный парсинг:

### Исправленный код:
```python
vk_chat_id = query.data.replace('quick_chat_', '', 1)
```

## 📝 Исправленные файлы

### 1. `domains/chats/handlers.py`
- ✅ `quick_chat_handler` - исправлен парсинг `quick_chat_`
- ✅ `quick_create_handler` - исправлен парсинг `quick_create_`
- ✅ `chat_settings_handler` - исправлен парсинг `chat_settings_`
- ✅ `chat_stats_handler` - исправлен парсинг `chat_stats_`
- ✅ `load_messages_handler` - исправлен парсинг `load_messages_`
- ✅ `all_dates_handler` - исправлен парсинг `all_dates_`
- ✅ Удален дубликат `chat_stats_handler`

### 2. `domains/summaries/handlers.py`
- ✅ `check_summary_handler` - исправлен парсинг `check_summary_`
- ✅ `publish_summary_handler` - исправлен парсинг `publish_summary_`
- ✅ `publish_summary_html_handler` - исправлен парсинг `publish_summary_html_`
- ✅ `publish_menu_handler` - исправлен парсинг `publish_menu_`

### 3. `domains/handlers_manager.py`
- ✅ `_handle_chat_advanced` - исправлен парсинг `chat_advanced_`

## 🧪 Тестирование

### Сценарий:
1. Пользователь заходит в чат
2. Нажимает "📋 Смотреть" (просмотр суммаризаций)
3. Нажимает "🔙 Назад"

### Ожидаемый результат:
✅ Кнопка "Назад" должна вернуть пользователя в меню чата

### Техническая проверка:
- `callback_data = "quick_chat_123_456"`
- `query.data.replace('quick_chat_', '', 1)` = `"123_456"` ✅
- `quick_chat_handler` получает правильный `vk_chat_id` ✅

## 🎯 Результат
**Кнопка "Назад" из просмотра суммаризации теперь работает правильно!**

Все обработчики теперь корректно парсят `vk_chat_id` с подчеркиваниями.
