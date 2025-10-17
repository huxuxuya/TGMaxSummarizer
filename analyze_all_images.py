#!/usr/bin/env python3
"""
Скрипт для анализа всех скачанных изображений с помощью локальной Llama через Ollama API
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
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
                    logger.error(f"❌ Ошибка получения моделей: HTTP {response.status}")
                    return []
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Ollama: {e}")
        return []

def encode_image_to_base64(image_path: str) -> str:
    """Кодировать изображение в base64"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"❌ Ошибка при кодировании изображения {image_path}: {e}")
        return None

async def analyze_image_with_ollama(base_url: str, model_name: str, image_path: str, prompt: str = None) -> str:
    """Анализировать изображение с помощью Ollama"""
    
    if prompt is None:
        prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    # Кодируем изображение в base64
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
                    logger.error(f"❌ Ошибка API для {image_path}: HTTP {response.status}")
                    error_text = await response.text()
                    logger.error(f"Детали ошибки: {error_text}")
                    return None
    except asyncio.TimeoutError:
        logger.error(f"❌ Таймаут при анализе изображения {image_path}")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе изображения {image_path}: {e}")
        return None

def find_all_images(images_dir: str = "images") -> List[Path]:
    """Найти все изображения в директории"""
    images_path = Path(images_dir)
    if not images_path.exists():
        logger.error(f"❌ Директория {images_dir} не найдена")
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    images = []
    
    for ext in image_extensions:
        images.extend(images_path.rglob(f"*{ext}"))
        images.extend(images_path.rglob(f"*{ext.upper()}"))
    
    return sorted(images)

def save_analysis_result(image_path: Path, analysis_text: str, model_name: str):
    """Сохранить результат анализа в текстовый файл"""
    try:
        # Создаем имя файла для результата анализа
        result_path = image_path.with_suffix('.txt')
        
        # Подготавливаем содержимое файла
        content = f"""Анализ изображения: {image_path.name}
Модель: {model_name}
Дата анализа: {asyncio.get_event_loop().time()}
Путь к изображению: {image_path}

РЕЗУЛЬТАТ АНАЛИЗА:
{analysis_text}
"""
        
        # Сохраняем файл
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Результат сохранен: {result_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения результата для {image_path}: {e}")
        return False

def print_models_menu(models: list):
    """Вывести меню выбора моделей"""
    logger.info(f"\n✅ Найдено {len(models)} моделей:")
    for i, model in enumerate(models, 1):
        logger.info(f"  {i}. {model}")

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

async def analyze_all_images(model_name: str, custom_prompt: str = None, max_images: int = None):
    """Анализировать все найденные изображения"""
    logger.info("🔍 Поиск изображений...")
    images = find_all_images()
    
    if not images:
        logger.error("❌ Изображения не найдены")
        return
    
    logger.info(f"📁 Найдено {len(images)} изображений")
    
    if max_images:
        images = images[:max_images]
        logger.info(f"🔢 Ограничиваем анализ первыми {max_images} изображениями")
    
    # Статистика
    stats = {
        'total': len(images),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }
    
    logger.info(f"\n🚀 Начинаем анализ {stats['total']} изображений...")
    logger.info(f"🤖 Модель: {model_name}")
    if custom_prompt:
        logger.info(f"📝 Промт: {custom_prompt}")
    else:
        logger.info("📝 Используется стандартный промт")
    
    for i, image_path in enumerate(images, 1):
        logger.info(f"\n--- Изображение {i}/{stats['total']}: {image_path.name} ---")
        
        # Проверяем, не существует ли уже файл с результатом
        result_path = image_path.with_suffix('.txt')
        if result_path.exists():
            logger.info(f"⏭️ Пропускаем (уже проанализировано): {result_path.name}")
            stats['skipped'] += 1
            continue
        
        stats['processed'] += 1
        
        # Анализируем изображение
        logger.info(f"🖼️ Анализируем: {image_path}")
        analysis_result = await analyze_image_with_ollama(
            OLLAMA_BASE_URL, 
            model_name, 
            str(image_path), 
            custom_prompt
        )
        
        if analysis_result:
            # Сохраняем результат
            if save_analysis_result(image_path, analysis_result, model_name):
                stats['successful'] += 1
                logger.info(f"✅ Успешно проанализировано: {image_path.name}")
            else:
                stats['failed'] += 1
        else:
            stats['failed'] += 1
            logger.error(f"❌ Не удалось проанализировать: {image_path.name}")
        
        # Небольшая пауза между запросами
        await asyncio.sleep(1)
    
    # Итоговая статистика
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВАЯ СТАТИСТИКА:")
    logger.info("=" * 60)
    logger.info(f"   Всего изображений: {stats['total']}")
    logger.info(f"   Обработано: {stats['processed']}")
    logger.info(f"   Успешно проанализировано: {stats['successful']}")
    logger.info(f"   Пропущено (уже есть): {stats['skipped']}")
    logger.info(f"   Ошибок: {stats['failed']}")
    
    if stats['processed'] > 0:
        success_rate = (stats['successful'] / stats['processed']) * 100
        logger.info(f"   Успешность: {success_rate:.1f}%")
    
    logger.info("=" * 60)

async def main():
    """Основная функция"""
    logger.info("🖼️ Анализатор всех скачанных изображений")
    logger.info("=" * 60)
    
    # Проверяем наличие директории с изображениями
    images_dir = Path("images")
    if not images_dir.exists():
        logger.error("❌ Директория 'images' не найдена")
        logger.info("💡 Убедитесь, что изображения скачаны в директорию 'images'")
        return
    
    logger.info(f"📁 Директория изображений: {images_dir.resolve()}")
    logger.info(f"🌐 Ollama URL: {OLLAMA_BASE_URL}")
    
    # Получаем список моделей
    logger.info(f"\n🔍 Получаем список моделей с сервера {OLLAMA_BASE_URL}...")
    available_models = await get_available_models(OLLAMA_BASE_URL)
    
    if not available_models:
        logger.error("❌ Не удалось получить список моделей или сервер недоступен")
        logger.info("💡 Убедитесь, что Ollama запущен и доступен по адресу:", OLLAMA_BASE_URL)
        return
    
    # Выбираем модель
    print_models_menu(available_models)
    selected_model = select_model(available_models)
    
    logger.info(f"\n✅ Выбрана модель: {selected_model}")
    
    # Запрашиваем пользовательский промт
    print("\n📝 Введите промт для анализа изображений (или нажмите Enter для стандартного):")
    custom_prompt = input().strip()
    
    if not custom_prompt:
        custom_prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
        logger.info(f"📝 Используется стандартный промт: {custom_prompt}")
    
    # Спрашиваем о лимите изображений
    print("\n🔢 Введите максимальное количество изображений для анализа (или нажмите Enter для всех):")
    max_images_input = input().strip()
    
    max_images = None
    if max_images_input:
        try:
            max_images = int(max_images_input)
            if max_images <= 0:
                logger.warning("⚠️ Некорректное число, анализируем все изображения")
                max_images = None
        except ValueError:
            logger.warning("⚠️ Некорректный ввод, анализируем все изображения")
            max_images = None
    
    # Запускаем анализ
    await analyze_all_images(selected_model, custom_prompt, max_images)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⏹️ Анализ прерван пользователем")
    except Exception as e:
        logger.error(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
