#!/usr/bin/env python3
"""
Скрипт для анализа всех скачанных изображений с помощью gemma3:27b в 5 потоков
"""

import asyncio
import base64
import os
from pathlib import Path
import logging
from typing import List, Tuple
import time

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
MODEL_NAME = 'gemma3:27b'
MAX_CONCURRENT = 5  # Количество параллельных потоков

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
                timeout=180  # Увеличиваем таймаут для больших изображений
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

async def process_single_image(image_path: Path, prompt: str, model_name: str, base_url: str) -> Tuple[Path, bool, str]:
    """Обработать одно изображение"""
    try:
        # Проверяем, не существует ли уже файл с результатом
        result_path = image_path.with_suffix('.txt')
        if result_path.exists():
            return image_path, True, "уже проанализировано"
        
        # Анализируем изображение
        analysis_result = await analyze_image_with_ollama(
            base_url, 
            model_name, 
            str(image_path), 
            prompt
        )
        
        if analysis_result:
            # Сохраняем результат
            if save_analysis_result(image_path, analysis_result, model_name):
                return image_path, True, "успешно проанализировано"
            else:
                return image_path, False, "ошибка сохранения"
        else:
            return image_path, False, "ошибка анализа"
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при обработке {image_path}: {e}")
        return image_path, False, f"критическая ошибка: {e}"

async def process_images_batch(images_batch: List[Path], prompt: str, model_name: str, base_url: str, batch_num: int) -> List[Tuple[Path, bool, str]]:
    """Обработать пакет изображений"""
    logger.info(f"🚀 Поток {batch_num}: начинаем обработку {len(images_batch)} изображений")
    
    results = []
    for i, image_path in enumerate(images_batch, 1):
        logger.info(f"🖼️ Поток {batch_num}: {i}/{len(images_batch)} - {image_path.name}")
        
        result = await process_single_image(image_path, prompt, model_name, base_url)
        results.append(result)
        
        # Небольшая пауза между запросами в потоке
        await asyncio.sleep(0.5)
    
    logger.info(f"✅ Поток {batch_num}: завершен")
    return results

def split_into_batches(images: List[Path], batch_size: int) -> List[List[Path]]:
    """Разделить список изображений на пакеты"""
    batches = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batches.append(batch)
    return batches

async def analyze_all_images_parallel(max_images: int = None):
    """Анализировать все найденные изображения параллельно"""
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
    
    prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    logger.info(f"\n🚀 Начинаем параллельный анализ {stats['total']} изображений...")
    logger.info(f"🤖 Модель: {MODEL_NAME}")
    logger.info(f"📝 Промт: {prompt}")
    logger.info(f"⚡ Параллельных потоков: {MAX_CONCURRENT}")
    
    # Разделяем изображения на пакеты для параллельной обработки
    batch_size = max(1, len(images) // MAX_CONCURRENT)
    image_batches = split_into_batches(images, batch_size)
    
    logger.info(f"📦 Создано {len(image_batches)} пакетов для обработки")
    
    start_time = time.time()
    
    # Создаем задачи для параллельной обработки
    tasks = []
    for i, batch in enumerate(image_batches, 1):
        task = process_images_batch(batch, prompt, MODEL_NAME, OLLAMA_BASE_URL, i)
        tasks.append(task)
    
    # Запускаем все задачи параллельно
    logger.info("⚡ Запускаем параллельную обработку...")
    all_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Обрабатываем результаты
    for batch_results in all_results:
        if isinstance(batch_results, Exception):
            logger.error(f"❌ Ошибка в пакете: {batch_results}")
            continue
            
        for image_path, success, message in batch_results:
            stats['processed'] += 1
            if success:
                if "уже проанализировано" in message:
                    stats['skipped'] += 1
                else:
                    stats['successful'] += 1
            else:
                stats['failed'] += 1
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Итоговая статистика
    logger.info("\n" + "=" * 60)
    logger.info("📊 ИТОГОВАЯ СТАТИСТИКА:")
    logger.info("=" * 60)
    logger.info(f"   Всего изображений: {stats['total']}")
    logger.info(f"   Обработано: {stats['processed']}")
    logger.info(f"   Успешно проанализировано: {stats['successful']}")
    logger.info(f"   Пропущено (уже есть): {stats['skipped']}")
    logger.info(f"   Ошибок: {stats['failed']}")
    logger.info(f"   Время обработки: {processing_time:.1f} секунд")
    
    if stats['processed'] > 0:
        success_rate = (stats['successful'] / stats['processed']) * 100
        logger.info(f"   Успешность: {success_rate:.1f}%")
        
        if processing_time > 0:
            images_per_second = stats['processed'] / processing_time
            logger.info(f"   Скорость: {images_per_second:.2f} изображений/сек")
    
    logger.info("=" * 60)

async def main():
    """Основная функция"""
    logger.info("🖼️ Параллельный анализатор всех скачанных изображений с gemma3:27b")
    logger.info("=" * 60)
    
    # Проверяем наличие директории с изображениями
    images_dir = Path("images")
    if not images_dir.exists():
        logger.error("❌ Директория 'images' не найдена")
        logger.info("💡 Убедитесь, что изображения скачаны в директорию 'images'")
        return
    
    logger.info(f"📁 Директория изображений: {images_dir.resolve()}")
    logger.info(f"🌐 Ollama URL: {OLLAMA_BASE_URL}")
    logger.info(f"🤖 Модель: {MODEL_NAME}")
    logger.info(f"⚡ Параллельных потоков: {MAX_CONCURRENT}")
    
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
    await analyze_all_images_parallel(max_images)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⏹️ Анализ прерван пользователем")
    except Exception as e:
        logger.error(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
