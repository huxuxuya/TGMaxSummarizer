# VK MAX Telegram Bot - Новая Архитектура

## Обзор

Telegram бот для анализа чатов VK MAX с использованием современной domain-driven архитектуры.

## Структура проекта

```
TGMaxSummarizer/
├── domains/                    # Domain-специфичная логика
│   ├── users/                 # Пользователи и их настройки
│   ├── chats/                 # Чаты и сообщения
│   ├── ai/                    # AI анализ и pipelines
│   └── summaries/             # Суммаризации
├── core/                      # Основная инфраструктура
│   ├── config/               # Конфигурация с Pydantic
│   ├── database/             # Работа с БД
│   └── exceptions.py         # Кастомные исключения
├── infrastructure/           # Внешние сервисы
│   ├── vk/                  # VK MAX API
│   ├── telegram/            # Telegram API
│   └── ai_providers/        # AI провайдеры
├── shared/                   # Общие утилиты
│   ├── utils.py
│   ├── constants.py
│   └── prompts.py
└── bot_new.py               # Главный файл бота
```

## Ключевые улучшения

### 1. Domain-Driven Design
- Каждый домен (users, chats, ai, summaries) изолирован
- Четкое разделение ответственности
- Легко тестируемые компоненты

### 2. Repository Pattern
- Изоляция работы с базой данных
- Единообразный интерфейс для всех сущностей
- Легкая замена источника данных

### 3. Pipeline Pattern для AI
- Модульные этапы анализа
- Гибкая композиция pipelines
- Легкое добавление новых типов анализа

### 4. Pydantic Configuration
- Type-safe конфигурация
- Автоматическая валидация
- Четкие схемы данных

### 5. Dependency Injection
- Слабая связанность компонентов
- Легкое тестирование
- Гибкая архитектура

## Установка

1. Установите зависимости:
```bash
pip install -r requirements_new.txt
```

2. Создайте файл `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
VK_MAX_TOKEN=your_vk_max_token
GIGACHAT_API_KEY=your_gigachat_key
OPENAI_API_KEY=your_openai_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
DEFAULT_AI_PROVIDER=ollama
ENABLE_REFLECTION=true
AUTO_IMPROVE_SUMMARY=false
ENABLE_LLM_LOGGING=true
```

3. Запустите бота:
```bash
python bot_new.py
```

## Использование

1. Добавьте бота в Telegram группу
2. Сделайте бота администратором
3. Используйте `/start` в личных сообщениях
4. Выберите группу и начните управление чатами

## AI Pipelines

### SummarizationPipeline
Базовая суммаризация чатов

### ReflectionPipeline  
Анализ и улучшение суммаризаций

### StructuredAnalysisPipeline
Классификация → Экстракция → Сводка

### DataCleaningPipeline
Очистка и фильтрация сообщений

## Конфигурация

Все настройки в `core/config/` с автоматической валидацией:

- `AIConfig` - настройки AI провайдеров
- `DatabaseConfig` - настройки БД
- `BotConfig` - настройки бота

## Тестирование

Каждый компонент можно тестировать изолированно:

```python
from domains.users.service import UserService
from core.database.connection import DatabaseConnection

# Тест сервиса пользователей
db = DatabaseConnection("test.db")
user_service = UserService(db)
# ... тесты
```

## Миграция со старой версии

1. Сохраните данные из старой БД
2. Запустите новую версию
3. БД будет создана автоматически
4. Импортируйте данные при необходимости

## Производительность

- Асинхронная обработка
- Кэширование провайдеров
- Оптимизированные запросы к БД
- Pipeline-параллелизм

## Безопасность

- Валидация всех входных данных
- Изоляция доменов
- Безопасная работа с БД
- Логирование всех операций

