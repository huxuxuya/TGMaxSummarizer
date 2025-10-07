# 🚀 Как запустить бота

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка токенов

### Вариант A: Файл .env
```bash
cp env_example_safe.txt .env
# Отредактируйте .env файл
```

### Вариант B: Переменные окружения
```bash
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
export GIGACHAT_API_KEY="your_gigachat_api_key_here"
export VK_MAX_TOKEN="your_vk_max_token_here"
```

## 3. Запуск бота

### Полный запуск (рекомендуется)
```bash
python start_bot.py
```

### Быстрый запуск
```bash
python quick_start.py
```

### Проверка статуса
```bash
python status_bot.py
```

### Остановка бота
```bash
python stop_bot.py
```

## 4. Получение токенов

### Telegram Bot Token
1. Напишите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

### VK MAX Token
1. Откройте приложение VK MAX
2. Перейдите в настройки → Разработчикам
3. Создайте токен доступа

### GigaChat API Key
1. Зайдите на https://developers.sber.ru/portal/products/gigachat
2. Зарегистрируйтесь
3. Создайте новый проект
4. Получите API ключ

## 5. Проверка работы

После запуска:
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Проверьте доступные команды

## 🆘 Решение проблем

### Бот не запускается
```bash
python status_bot.py  # Проверить статус
python stop_bot.py    # Остановить процессы
python start_bot.py   # Запустить заново
```

### Ошибки токенов
- Проверьте правильность токенов
- Убедитесь, что токены активны
- Проверьте переменные окружения

### Конфликты процессов
```bash
python stop_bot.py  # Остановить все процессы
```

## 📱 Использование

После запуска бот будет доступен в Telegram:
- `/start` - Начать работу
- `/help` - Справка
- `/chats` - Список чатов
- `/analyze` - Анализ чата

---

**Готово! Бот запущен и готов к работе!** 🎉