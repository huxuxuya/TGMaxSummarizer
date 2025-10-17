#!/usr/bin/env python3
"""
🖼️ Просмотр загруженных изображений

Скрипт для просмотра и анализа уже загруженных изображений.
Запуск: python view_images.py
"""

import os
import json
from pathlib import Path
from typing import Dict, List

from shared.image_viewer import ImageViewer

def main():
    """Главная функция"""
    print("🖼️ ПРОСМОТР ЗАГРУЖЕННЫХ ИЗОБРАЖЕНИЙ")
    print("=" * 40)
    
    try:
        viewer = ImageViewer()
        
        # Получаем статистику
        print("\n📊 Статистика изображений:")
        stats = viewer.get_image_stats()
        
        print(f"   Всего изображений: {stats.get('total_images', 0)}")
        print(f"   Чатов с изображениями: {stats.get('chats_with_images', 0)}")
        print(f"   Общий размер: {stats.get('total_size_mb', 0):.2f} MB")
        
        # Показываем структуру папок
        images_path = Path("images")
        if not images_path.exists():
            print("\n❌ Папка images не найдена")
            return
        
        print(f"\n📁 Структура папок:")
        print(f"   Базовая папка: {images_path.absolute()}")
        
        chats_path = images_path / "chats"
        if chats_path.exists():
            chat_folders = [f for f in chats_path.iterdir() if f.is_dir()]
            
            if not chat_folders:
                print("   📁 Папка chats пустая")
            else:
                print(f"   📁 Найдено {len(chat_folders)} чатов с изображениями:")
                
                for chat_folder in sorted(chat_folders):
                    image_files = list(chat_folder.glob("*"))
                    total_size = sum(f.stat().st_size for f in image_files if f.is_file())
                    size_mb = total_size / (1024 * 1024)
                    
                    print(f"      📂 {chat_folder.name}: {len(image_files)} файлов ({size_mb:.2f} MB)")
                    
                    # Показываем первые несколько файлов
                    for i, img_file in enumerate(sorted(image_files)[:3]):
                        if img_file.is_file():
                            size_kb = img_file.stat().st_size / 1024
                            print(f"         🖼️ {img_file.name} ({size_kb:.1f} KB)")
                    
                    if len(image_files) > 3:
                        print(f"         ... и еще {len(image_files) - 3} файлов")
        else:
            print("   📁 Папка chats не найдена")
        
        # Показываем детали по чатам
        print(f"\n🔍 Детали по чатам:")
        try:
            all_images = viewer.get_all_images()
            
            if not all_images:
                print("   Нет изображений для отображения")
            else:
                for chat_id, images in all_images.items():
                    print(f"   📱 Чат {chat_id}: {len(images)} изображений")
                    
                    for i, img_info in enumerate(images[:2]):  # Показываем первые 2
                        size_kb = img_info.get('size', 0) / 1024
                        print(f"      🖼️ {img_info.get('filename', 'unknown')} - {size_kb:.1f} KB")
                    
                    if len(images) > 2:
                        print(f"      ... и еще {len(images) - 2} изображений")
        
        except Exception as e:
            print(f"   ⚠️ Ошибка получения деталей: {e}")
        
        # Показываем файлы в корне images
        print(f"\n📄 Файлы в корне images:")
        root_files = [f for f in images_path.iterdir() if f.is_file()]
        
        if not root_files:
            print("   Нет файлов в корне")
        else:
            for file in root_files:
                size_kb = file.stat().st_size / 1024
                print(f"   📄 {file.name} ({size_kb:.1f} KB)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
