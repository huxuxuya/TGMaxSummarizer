"""
LogSession - централизованное логирование шагов с детерминированным порядком
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LogSession:
    """Сеанс логирования с монотонным счетчиком и манифестом"""
    
    def __init__(self, base_path: Path, run_meta: Dict[str, Any]):
        self.base_path = base_path
        self.sequence = 0
        self.manifest_path = base_path / "manifest.json"
        self.lock = asyncio.Lock()
        self.run_meta = run_meta
        self._init_manifest()
    
    def _init_manifest(self):
        """Инициализировать манифест с метаданными запуска"""
        manifest_data = {
            "run_meta": self.run_meta,
            "steps": [],
            "created_at": datetime.now().isoformat(),
            "sequence_counter": 0
        }
        
        try:
            with open(self.manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"📋 Манифест инициализирован: {self.manifest_path}")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации манифеста: {e}")
    
    async def log_phase(self, step: str, phase: str, content: str, meta: Optional[Dict[str, Any]] = None) -> str:
        """
        Логировать фазу шага с атомарной записью
        
        Args:
            step: Название шага (cleaning, summarization, reflection, etc.)
            phase: Фаза (request, response)
            content: Содержимое для записи
            meta: Дополнительные метаданные
            
        Returns:
            Путь к созданному файлу
        """
        async with self.lock:
            self.sequence += 1
            seq = f"{self.sequence:02d}"
            filename = f"{seq}_{step}_{phase}.txt"
            
            # Атомарная запись файла
            await self._write_atomic(filename, content)
            
            # Обновление манифеста
            entry = {
                "seq": self.sequence,
                "step": step,
                "phase": phase,
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "monotonic_time": time.monotonic_ns(),
                **(meta or {})
            }
            await self._append_manifest(entry)
            
            logger.debug(f"📝 Логирован {step}/{phase} -> {filename}")
            return str(self.base_path / filename)
    
    async def _write_atomic(self, filename: str, content: str):
        """Атомарная запись файла через временное имя"""
        temp_path = self.base_path / f".{filename}.tmp"
        final_path = self.base_path / filename
        
        try:
            # Записываем во временный файл
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Атомарно переименовываем
            temp_path.replace(final_path)
            
        except Exception as e:
            # Очищаем временный файл при ошибке
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    async def _append_manifest(self, entry: Dict[str, Any]):
        """Атомарно добавить запись в манифест"""
        try:
            # Читаем текущий манифест
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
            else:
                manifest_data = {"run_meta": self.run_meta, "steps": [], "created_at": datetime.now().isoformat()}
            
            # Добавляем новую запись
            manifest_data["steps"].append(entry)
            manifest_data["sequence_counter"] = self.sequence
            manifest_data["updated_at"] = datetime.now().isoformat()
            
            # Атомарно записываем обновленный манифест
            temp_manifest = self.manifest_path.with_suffix('.tmp')
            with open(temp_manifest, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, ensure_ascii=False, indent=2)
            
            temp_manifest.replace(self.manifest_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления манифеста: {e}")
    
    def get_manifest(self) -> Dict[str, Any]:
        """Получить текущий манифест"""
        try:
            if self.manifest_path.exists():
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"❌ Ошибка чтения манифеста: {e}")
        
        return {"run_meta": self.run_meta, "steps": [], "created_at": datetime.now().isoformat()}
    
    def get_sequence(self) -> int:
        """Получить текущий номер последовательности"""
        return self.sequence

