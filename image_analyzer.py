#!/usr/bin/env python3
"""
Скрипт для анализа изображений с помощью локальной Llama через Ollama API
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import aiohttp

# Настройка базового URL для Ollama
os.environ['OLLAMA_BASE_URL'] = 'http://192.168.1.75:11434'
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.75:11434')

async def get_available_models(base_url: str) -> list:
    """Получить список доступных моделей из Ollama"""
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

def encode_image_to_base64(image_path: str) -> str:
    """Кодировать изображение в base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Ошибка при кодировании изображения: {e}")
        return None

async def analyze_image_with_ollama(base_url: str, model_name: str, image_path: str, prompt: str = None):
    """Анализировать изображение с помощью Ollama"""
    
    if prompt is None:
        prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    # Кодируем изображение в base64
    print("🖼️  Кодирование изображения...")
    image_base64 = encode_image_to_base64(image_path)
    if not image_base64:
        return None
    
    # Подготавливаем данные для запроса
    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    print(f"🤖 Отправка запроса к модели {model_name}...")
    print(f"📝 Промт: {prompt}")
    print("-" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=120  # Увеличиваем таймаут для анализа изображений
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('response', '')
                else:
                    print(f"❌ Ошибка API: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Детали ошибки: {error_text}")
                    return None
    except asyncio.TimeoutError:
        print("❌ Таймаут при анализе изображения")
        return None
    except Exception as e:
        print(f"❌ Ошибка при анализе изображения: {e}")
        return None

def print_models_menu(models: list):
    """Вывести меню выбора моделей"""
    print(f"\n✅ Найдено {len(models)} моделей:")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")

def select_model(models: list) -> str:
    """Выбрать модель из списка"""
    while True:
        try:
            choice = input(f"\nВыберите модель (1-{len(models)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(models):
                return models[choice_num - 1]
            else:
                print(f"❌ Введите число от 1 до {len(models)}")
        except ValueError:
            print("❌ Введите корректное число")

async def main():
    """Основная функция"""
    print("🖼️  Анализатор изображений с помощью локальной Llama")
    print("=" * 60)
    
    # Путь к изображению
    image_path = "IMG_7388.jpg"
    
    # Проверяем существование файла
    if not os.path.exists(image_path):
        print(f"❌ Файл изображения не найден: {image_path}")
        print("💡 Убедитесь, что файл IMG_7386.JPG находится в текущей директории")
        return
    
    print(f"📁 Изображение: {image_path}")
    print(f"🌐 Ollama URL: {OLLAMA_BASE_URL}")
    
    # Получаем список моделей
    print(f"\n🔍 Получаем список моделей с сервера {OLLAMA_BASE_URL}...")
    available_models = await get_available_models(OLLAMA_BASE_URL)
    
    if not available_models:
        print("❌ Не удалось получить список моделей или сервер недоступен")
        print("💡 Убедитесь, что Ollama запущен и доступен по адресу:", OLLAMA_BASE_URL)
        return
    
    # Выбираем модель
    print_models_menu(available_models)
    selected_model = select_model(available_models)
    
    print(f"\n✅ Выбрана модель: {selected_model}")
    
    # Запрашиваем пользовательский промт
    print("\n📝 Введите промт для анализа изображения (или нажмите Enter для стандартного):")
    custom_prompt = input().strip()
    
    if not custom_prompt:
        custom_prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
        print(f"📝 Используется стандартный промт: {custom_prompt}")
    
    # Анализируем изображение
    print("\n🚀 Начинаем анализ изображения...")
    result = await analyze_image_with_ollama(OLLAMA_BASE_URL, selected_model, image_path, custom_prompt)
    
    if result:
        print("\n" + "=" * 60)
        print("📋 РЕЗУЛЬТАТ АНАЛИЗА:")
        print("=" * 60)
        print(result)
        print("=" * 60)
    else:
        print("\n❌ Не удалось проанализировать изображение")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Анализ прерван пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
