#!/usr/bin/env python3
"""
Скрипт для сравнения производительности анализа изображений с разным количеством потоков
"""

import asyncio
import base64
import os
from pathlib import Path
import logging
import time
from typing import List

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

def save_analysis_result(image_path: Path, analysis_text: str, model_name: str, thread_count: int):
    """Сохранить результат анализа в текстовый файл"""
    try:
        result_path = image_path.parent / f"{image_path.stem}_threads_{thread_count}.txt"
        
        content = f"""Анализ изображения: {image_path.name}
Модель: {model_name}
Потоков: {thread_count}
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

async def process_single_image_with_semaphore(semaphore: asyncio.Semaphore, image_path: Path, prompt: str, model_name: str, base_url: str, thread_count: int, stats: dict) -> None:
    """Обработать одно изображение с семафором"""
    async with semaphore:  # Ограничиваем количество одновременных запросов
        try:
            # Проверяем, не существует ли уже файл с результатом для этого количества потоков
            result_path = image_path.parent / f"{image_path.stem}_threads_{thread_count}.txt"
            if result_path.exists():
                stats['skipped'] += 1
                logger.info(f"⏭️ Пропускаем (уже проанализировано): {image_path.name}")
                return
            
            stats['processed'] += 1
            logger.info(f"🖼️ [{thread_count} потоков] Анализируем: {image_path.name} ({stats['processed']}/{stats['total']})")
            
            # Анализируем изображение
            analysis_result = await analyze_image_with_ollama(
                base_url, 
                model_name, 
                str(image_path), 
                prompt
            )
            
            if analysis_result:
                # Сохраняем результат
                if save_analysis_result(image_path, analysis_result, model_name, thread_count):
                    stats['successful'] += 1
                    logger.info(f"✅ [{thread_count} потоков] Успешно проанализировано: {image_path.name}")
                else:
                    stats['failed'] += 1
                    logger.error(f"❌ [{thread_count} потоков] Ошибка сохранения: {image_path.name}")
            else:
                stats['failed'] += 1
                logger.error(f"❌ [{thread_count} потоков] Не удалось проанализировать: {image_path.name}")
                
        except Exception as e:
            stats['failed'] += 1
            logger.error(f"❌ [{thread_count} потоков] Критическая ошибка при обработке {image_path}: {e}")

async def benchmark_with_threads(images: List[Path], thread_count: int, max_images: int = 10):
    """Бенчмарк с определенным количеством потоков"""
    logger.info(f"\n🚀 БЕНЧМАРК С {thread_count} ПОТОКАМИ")
    logger.info("=" * 50)
    
    # Ограничиваем количество изображений
    test_images = images[:max_images]
    
    # Статистика
    stats = {
        'total': len(test_images),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }
    
    prompt = "Что изображено на этой картинке? Опиши подробно, что ты видишь."
    
    logger.info(f"📁 Тестируем на {len(test_images)} изображениях")
    logger.info(f"🤖 Модель: {MODEL_NAME}")
    logger.info(f"⚡ Потоков: {thread_count}")
    
    # Создаем семафор для ограничения количества одновременных запросов
    semaphore = asyncio.Semaphore(thread_count)
    
    start_time = time.time()
    
    # Создаем задачи для всех изображений
    tasks = []
    for image_path in test_images:
        task = process_single_image_with_semaphore(
            semaphore, image_path, prompt, MODEL_NAME, OLLAMA_BASE_URL, thread_count, stats
        )
        tasks.append(task)
    
    # Запускаем все задачи
    logger.info(f"⚡ Запускаем обработку с {thread_count} потоками...")
    await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Статистика для этого бенчмарка
    logger.info(f"\n📊 РЕЗУЛЬТАТЫ ДЛЯ {thread_count} ПОТОКОВ:")
    logger.info("=" * 50)
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
    
    return {
        'thread_count': thread_count,
        'total_images': stats['total'],
        'processed': stats['processed'],
        'successful': stats['successful'],
        'failed': stats['failed'],
        'skipped': stats['skipped'],
        'processing_time': processing_time,
        'images_per_second': stats['processed'] / processing_time if processing_time > 0 else 0,
        'success_rate': (stats['successful'] / stats['processed']) * 100 if stats['processed'] > 0 else 0
    }

async def main():
    """Основная функция"""
    logger.info("🖼️ БЕНЧМАРК АНАЛИЗА ИЗОБРАЖЕНИЙ С РАЗНЫМ КОЛИЧЕСТВОМ ПОТОКОВ")
    logger.info("=" * 70)
    
    # Проверяем наличие директории с изображениями
    images_dir = Path("images")
    if not images_dir.exists():
        logger.error("❌ Директория 'images' не найдена")
        logger.info("💡 Убедитесь, что изображения скачаны в директорию 'images'")
        return
    
    logger.info(f"📁 Директория изображений: {images_dir.resolve()}")
    logger.info(f"🌐 Ollama URL: {OLLAMA_BASE_URL}")
    logger.info(f"🤖 Модель: {MODEL_NAME}")
    
    # Находим все изображения
    logger.info("🔍 Поиск изображений...")
    all_images = find_all_images()
    
    if not all_images:
        logger.error("❌ Изображения не найдены")
        return
    
    logger.info(f"📁 Найдено {len(all_images)} изображений")
    
    # Спрашиваем о количестве изображений для теста
    print(f"\n🔢 Введите количество изображений для теста (максимум {len(all_images)}, по умолчанию 10):")
    max_images_input = input().strip()
    
    max_images = 10
    if max_images_input:
        try:
            max_images = int(max_images_input)
            if max_images <= 0 or max_images > len(all_images):
                logger.warning(f"⚠️ Некорректное число, используем 10 изображений")
                max_images = 10
        except ValueError:
            logger.warning("⚠️ Некорректный ввод, используем 10 изображений")
            max_images = 10
    
    # Спрашиваем о количестве потоков для тестирования
    print("\n⚡ Введите количество потоков для тестирования (например: 3,10 или просто 3):")
    threads_input = input().strip()
    
    thread_counts = [3, 10]  # По умолчанию
    if threads_input:
        try:
            if ',' in threads_input:
                thread_counts = [int(x.strip()) for x in threads_input.split(',')]
            else:
                thread_counts = [int(threads_input)]
            
            # Проверяем корректность
            thread_counts = [t for t in thread_counts if t > 0 and t <= 20]
            if not thread_counts:
                thread_counts = [3, 10]
        except ValueError:
            logger.warning("⚠️ Некорректный ввод, используем 3 и 10 потоков")
            thread_counts = [3, 10]
    
    logger.info(f"🔢 Тестируем на {max_images} изображениях")
    logger.info(f"⚡ Количество потоков для тестирования: {thread_counts}")
    
    # Запускаем бенчмарки
    results = []
    for thread_count in thread_counts:
        result = await benchmark_with_threads(all_images, thread_count, max_images)
        results.append(result)
        
        # Пауза между тестами
        logger.info(f"⏸️ Пауза 5 секунд перед следующим тестом...")
        await asyncio.sleep(5)
    
    # Сравнительная таблица результатов
    logger.info("\n" + "=" * 70)
    logger.info("📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ")
    logger.info("=" * 70)
    logger.info(f"{'Потоков':<8} {'Время (сек)':<12} {'Скорость (изоб/сек)':<20} {'Успешность (%)':<15}")
    logger.info("-" * 70)
    
    for result in results:
        logger.info(f"{result['thread_count']:<8} {result['processing_time']:<12.1f} {result['images_per_second']:<20.2f} {result['success_rate']:<15.1f}")
    
    # Анализ результатов
    logger.info("\n📈 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    if len(results) >= 2:
        fastest = min(results, key=lambda x: x['processing_time'])
        most_efficient = max(results, key=lambda x: x['images_per_second'])
        
        logger.info(f"🏆 Самый быстрый: {fastest['thread_count']} потоков ({fastest['processing_time']:.1f} сек)")
        logger.info(f"⚡ Самый эффективный: {most_efficient['thread_count']} потоков ({most_efficient['images_per_second']:.2f} изоб/сек)")
        
        if len(results) == 2 and results[0]['images_per_second'] > 0:
            improvement = ((results[1]['images_per_second'] - results[0]['images_per_second']) / results[0]['images_per_second']) * 100
            logger.info(f"📊 Улучшение производительности: {improvement:+.1f}%")
    
    logger.info("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n\n⏹️ Бенчмарк прерван пользователем")
    except Exception as e:
        logger.error(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
