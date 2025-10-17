#!/usr/bin/env python3
"""
Тестовый скрипт для анализа нескольких изображений
"""

import asyncio
import base64
import os
from pathlib import Path
import logging

import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Настройка базового URL для Ollama
OLLAMA_BASE_URL = 'http://192.168.1.75:11434'

async def analyze_image_with_ollama(base_url: str, model_name: str, image_path: str, prompt: str = None) -> str:
    """Анализировать изображение с помощью Ollama"""
    
    if prompt is None:
        prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    # Кодируем изображение в base64
    try:
        with open(image_path, "rb") as image_file:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"❌ Ошибка при кодировании изображения {image_path}: {e}")
        return None
    
    # Подготавливаем данные для запроса
    payload = {
        "model": model_name,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}/api/generate",
                json=payload,
                timeout=120
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('response', '')
                else:
                    logger.error(f"❌ Ошибка API для {image_path}: HTTP {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения {image_path}: {e}")
        return None

def save_analysis_result(image_path: Path, analysis_text: str, model_name: str):
    """Сохранить результат анализа в текстовый файл"""
    try:
        result_path = image_path.with_suffix('.txt')
        
        content = f"""Анализ изображения: {image_path.name}
Модель: {model_name}
Путь к изображению: {image_path}

РЕЗУЛЬТАТ АНАЛИЗА:
{analysis_text}
"""
        
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Результат сохранен: {result_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения результата для {image_path}: {e}")
        return False

async def test_analysis():
    """Тестируем анализ на нескольких изображениях"""
    logger.info("🧪 ТЕСТ АНАЛИЗА ИЗОБРАЖЕНИЙ")
    logger.info("=" * 50)
    
    # Находим первые 3 изображения для теста
    images_dir = Path("images")
    if not images_dir.exists():
        logger.error("❌ Директория 'images' не найдена")
        return
    
    # Ищем изображения
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    test_images = []
    
    for ext in image_extensions:
        test_images.extend(images_dir.rglob(f"*{ext}"))
        if len(test_images) >= 3:
            break
    
    test_images = test_images[:3]  # Берем только первые 3
    
    if not test_images:
        logger.error("❌ Изображения не найдены")
        return
    
    logger.info(f"📁 Найдено {len(test_images)} изображений для теста")
    
    # Используем модель по умолчанию (можно изменить)
    model_name = "gemma3:27b"  # Попробуем эту модель
    
    prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    for i, image_path in enumerate(test_images, 1):
        logger.info(f"\n--- Тест {i}/{len(test_images)}: {image_path.name} ---")
        
        # Проверяем, не существует ли уже файл с результатом
        result_path = image_path.with_suffix('.txt')
        if result_path.exists():
            logger.info(f"⏭️ Пропускаем (уже проанализировано)")
            continue
        
        logger.info(f"🖼️ Анализируем: {image_path}")
        analysis_result = await analyze_image_with_ollama(
            OLLAMA_BASE_URL, 
            model_name, 
            str(image_path), 
            prompt
        )
        
        if analysis_result:
            if save_analysis_result(image_path, analysis_result, model_name):
                logger.info(f"✅ Успешно проанализировано: {image_path.name}")
                logger.info(f"📝 Результат: {analysis_result[:100]}...")
            else:
                logger.error(f"❌ Не удалось сохранить результат")
        else:
            logger.error(f"❌ Не удалось проанализировать: {image_path.name}")
        
        # Пауза между запросами
        await asyncio.sleep(2)
    
    logger.info("\n🎉 Тест завершен!")

if __name__ == "__main__":
    try:
        asyncio.run(test_analysis())
    except KeyboardInterrupt:
        logger.info("\n\n⏹️ Тест прерван пользователем")
    except Exception as e:
        logger.error(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
