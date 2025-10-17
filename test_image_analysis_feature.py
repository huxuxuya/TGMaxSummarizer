#!/usr/bin/env python3
"""
Тестовый скрипт для проверки функционала анализа изображений
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from core.app_context import get_app_context
from domains.chats.image_analysis_service import ImageAnalysisService
from domains.chats.repository import MessageRepository

async def main():
    print("🧪 Тестирование функционала анализа изображений\n")
    
    # Инициализация
    ctx = get_app_context()
    
    # Создаем сервис анализа
    image_service = ImageAnalysisService(
        ollama_base_url=ctx.config['bot'].ollama_base_url,
        default_model=ctx.config['bot'].default_image_analysis_model,
        default_prompt=ctx.config['bot'].default_image_analysis_prompt,
        max_concurrent=ctx.config['bot'].image_analysis_max_concurrent
    )
    
    message_repo = ctx.chat_service.message_repo
    
    print(f"✅ Настройки:")
    print(f"   Ollama URL: {ctx.config['bot'].ollama_base_url}")
    print(f"   Модель: {ctx.config['bot'].default_image_analysis_model}")
    print(f"   Промпт: {ctx.config['bot'].default_image_analysis_prompt[:50]}...")
    print()
    
    # Проверяем доступность Ollama
    print("🔍 Проверка доступности Ollama...")
    models = await image_service.get_available_models()
    if models:
        print(f"✅ Ollama доступен. Найдено моделей: {len(models)}")
        print(f"   Доступные модели: {', '.join(models[:5])}")
    else:
        print("❌ Ollama недоступен или нет моделей")
        return
    print()
    
    # Получаем сообщения с изображениями
    print("📊 Проверка сообщений с изображениями...")
    vk_chat_id = "-68245000186538"  # Тестовый чат
    
    messages_with_images = message_repo.get_messages_with_images(vk_chat_id)
    print(f"✅ Найдено сообщений с изображениями: {len(messages_with_images)}")
    
    if not messages_with_images:
        print("⚠️ Нет сообщений с изображениями для анализа")
        return
    
    # Показываем информацию о первом сообщении
    first_msg = messages_with_images[0]
    print(f"\n📝 Первое сообщение:")
    print(f"   ID: {first_msg.message_id}")
    print(f"   Дата: {first_msg.date}")
    print(f"   Изображений: {len(first_msg.image_paths)}")
    print(f"   Пути: {first_msg.image_paths}")
    print(f"   Уже проанализировано: {len(first_msg.image_analysis) if first_msg.image_analysis else 0}")
    print()
    
    # Проверяем существование файла изображения
    if first_msg.image_paths:
        image_path = Path("images") / first_msg.image_paths[0]
        if image_path.exists():
            print(f"✅ Файл изображения существует: {image_path}")
            print(f"   Размер: {image_path.stat().st_size / 1024:.1f} KB")
        else:
            print(f"❌ Файл изображения не найден: {image_path}")
            return
    print()
    
    # Тестируем анализ одного изображения
    print("🖼️ Тестирование анализа одного изображения...")
    test_image_path = "images/" + first_msg.image_paths[0]
    
    analysis_result = await image_service.analyze_image(
        test_image_path,
        model=None,  # Используем дефолтную модель
        prompt=None  # Используем дефолтный промпт
    )
    
    if analysis_result:
        print(f"✅ Анализ успешен!")
        print(f"\n📄 Результат анализа:")
        print(f"   {analysis_result[:200]}...")
        print()
    else:
        print("❌ Не удалось проанализировать изображение")
        return
    
    # Тестируем получение неанализированных сообщений
    print("🔍 Поиск неанализированных сообщений...")
    unanalyzed = await image_service.get_unanalyzed_messages(vk_chat_id, message_repo)
    print(f"✅ Найдено неанализированных сообщений: {len(unanalyzed)}")
    print()
    
    # Тестируем обновление анализа в БД
    print("💾 Тестирование сохранения результата в БД...")
    test_analysis_data = [{
        "image_path": first_msg.image_paths[0],
        "analysis": analysis_result,
        "analyzed_at": "2025-10-18T00:00:00",
        "model": ctx.config['bot'].default_image_analysis_model,
        "prompt": ctx.config['bot'].default_image_analysis_prompt
    }]
    
    success = message_repo.update_message_analysis(first_msg.message_id, test_analysis_data)
    if success:
        print("✅ Результат анализа сохранен в БД")
    else:
        print("❌ Не удалось сохранить результат в БД")
    print()
    
    # Проверяем статистику чата
    print("📊 Проверка статистики чата...")
    stats = message_repo.get_chat_stats(vk_chat_id)
    print(f"✅ Статистика:")
    print(f"   Всего сообщений: {stats.total_messages}")
    print(f"   Всего изображений: {stats.total_images}")
    print(f"   Проанализировано: {stats.analyzed_images}")
    print(f"   Не проанализировано: {stats.unanalyzed_images}")
    print()
    
    print("=" * 60)
    print("🎉 Все тесты пройдены успешно!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

