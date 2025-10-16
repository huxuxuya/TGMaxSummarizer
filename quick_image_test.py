#!/usr/bin/env python3
"""
Быстрый тест анализа изображения с предустановленной моделью
"""

import asyncio
import base64
import os
import sys

import aiohttp

# Настройки
os.environ['OLLAMA_BASE_URL'] = 'http://192.168.1.75:11434'
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.75:11434')
DEFAULT_MODEL = "llava"  # Популярная модель для анализа изображений
IMAGE_PATH = "IMG_7386.JPG"

def encode_image_to_base64(image_path: str) -> str:
    """Кодировать изображение в base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Ошибка при кодировании изображения: {e}")
        return None

async def quick_analyze():
    """Быстрый анализ изображения"""
    print("🖼️  Быстрый анализ изображения")
    print(f"📁 Изображение: {IMAGE_PATH}")
    print(f"🤖 Модель: {DEFAULT_MODEL}")
    print(f"🌐 URL: {OLLAMA_BASE_URL}")
    
    # Проверяем файл
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Файл не найден: {IMAGE_PATH}")
        return
    
    # Кодируем изображение
    print("\n🖼️  Кодирование изображения...")
    image_base64 = encode_image_to_base64(IMAGE_PATH)
    if not image_base64:
        return
    
    # Промт
    prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    # Данные для запроса
    payload = {
        "model": DEFAULT_MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    print(f"\n📝 Промт: {prompt}")
    print("🚀 Отправка запроса...")
    print("-" * 50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=120
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('response', '')
                    
                    print("\n" + "=" * 60)
                    print("📋 РЕЗУЛЬТАТ:")
                    print("=" * 60)
                    print(result)
                    print("=" * 60)
                else:
                    print(f"❌ Ошибка API: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Детали: {error_text}")
    except asyncio.TimeoutError:
        print("❌ Таймаут")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(quick_analyze())
    except KeyboardInterrupt:
        print("\n⏹️  Прервано")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
