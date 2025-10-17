#!/usr/bin/env python3
"""
🔍 Простой тест извлечения изображений

Тестируем извлечение URL изображений из реальных данных VK MAX.
"""

import asyncio
import logging
from shared.image_utils import ImageDownloader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_image_extraction():
    """Тестируем извлечение изображений на реальных данных"""
    logger.info("🔍 ТЕСТ ИЗВЛЕЧЕНИЯ ИЗОБРАЖЕНИЙ")
    logger.info("=" * 50)
    
    # Создаем ImageDownloader
    image_downloader = ImageDownloader()
    
    # Тестовые данные из реальных сообщений VK MAX
    test_attachments = [
        {
            'previewData': 'data:image/webp;base64,UklGRmgCAABXRUJQVlA4IFwCAACQDQCdASoyACYAAUAmJZQC9i+5pccrfo72gyiH4P+G+aX+H6iupq/7D+AfxjXIOEB/gPRD/lf4X/VeloN2o+3pQPpSD8cJeDZc8QJJ6I5ICTrgPllKphJa/HUH43txBheTzSSQ5CCdA6WWj10INBEZ1RL8o/wA/uNP/K5hhGFXpQ4glDbdTCxcPQzmOo4jbAiZyr493MQafxCJYNBY4YrN4DrykKCQh+/FCN4yeOuLMFmtwp5lQSWA8Ap0EAMntS7Q69c86itokJFn/FXk0D+9VdtsV1L/kXiZwR/2dS03u/rpopowQ/ys6GP+dW3a2rf1/EsyJcqpiNApUBrAx9itOpvDt+726k1ZbnACGgR/CHfHAVPyx9deFIu/cYLwZ3Q29WklJ7TQMOclipSRx8W1BcN+Tv8RNea6UhTOSS08SWF7a4cl5nANABri0ufPPLkkPsnhByv5g7j5Vek31/IBKsWJGmL6c46/x3+Z2SpvisdZZ7wqJhn0u9O8bvPqC90Rz1sBs3dRYwYYj/L+uTPb/wdcufuElzxqHlvwnrFP5qvhLrfI4/Y/geMrJTKXxwXXf9jwx05MizDJiuvkXP2pwG/JYyf+EorpUH4Cr7/U+g8SBAKk3QZJKVdapXH54jc3RMAuprS5BUpfyY/4puxDpWoSb6YYZmZ6gRbMeJjW//h7fFZihC3t6ImN08S5UmsP2gJKxsay3TI7x9MlvUg7yN3/2JI0NFL/4haJl02w3N6wrRiYEIeumoCWPIdQumY8iKlmHAUICKlqgdJGK/yfHFSo6gXKBa33/gAA',
            'baseUrl': 'https://i.oneme.ru/i?r=BTE2sh_eZW7g8kugOdIm2NotKNCK0vJe584qEM3ul-I3ejhVCRuCB9LweYBPUPqBvxc',
            'photoToken': '4JBhLJ5pZ+MmJ9TV3M++CB655cXTMRMHJtUSn3nM6DwvH/d94FMgd6QYoXBHRNRHUXFZCVaYHmdljMKlPxLAWhJKueAnNryqgjS/2tmr4EQ=',
            '_type': 'PHOTO',
            'width': 1920,
            'photoId': 186040132,
            'height': 1440
        }
    ]
    
    logger.info("📎 Тестовые attachments:")
    logger.info(f"   Количество: {len(test_attachments)}")
    logger.info(f"   Первый attachment: {test_attachments[0]}")
    
    # Тестируем извлечение URL
    try:
        image_urls = image_downloader.extract_image_urls(test_attachments)
        logger.info(f"🖼️ Извлечено URL изображений: {len(image_urls)}")
        
        for i, url in enumerate(image_urls):
            logger.info(f"  {i+1}. {url}")
        
        if image_urls:
            logger.info("✅ Тест прошел успешно! URL изображений извлечены.")
        else:
            logger.warning("⚠️ URL изображений не извлечены. Проверьте логику extract_image_urls.")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении URL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_extraction()
