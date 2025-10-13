"""
Ollama AI провайдер для локальных моделей
"""
import aiohttp
import json
from typing import List, Dict, Optional, Any
from .base_provider import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    """Провайдер для работы с локальными моделями через Ollama API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = config.get('OLLAMA_MODEL', 'gpt-oss:20b')
        self.timeout = config.get('OLLAMA_TIMEOUT', 120)  # Увеличенный таймаут для локальных моделей
        
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью Ollama
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
        """
        try:
            # Оптимизируем текст
            self.logger.info("🔧 Оптимизируем текст для Ollama...")
            optimized_messages = self.optimize_text(messages)
            
            # Форматируем для анализа
            formatted_text = self.format_messages_for_analysis(optimized_messages)
            
            # Логируем форматированные сообщения (ПОСЛЕ оптимизации)
            if self.llm_logger:
                self.llm_logger.log_formatted_messages(formatted_text, len(optimized_messages))
            
            self.logger.info(f"📊 Статистика для Ollama:")
            self.logger.info(f"   Всего сообщений: {len(messages)}")
            self.logger.info(f"   После оптимизации: {len(optimized_messages)}")
            self.logger.info(f"   Длина текста: {len(formatted_text)} символов")
            
            # Вызываем Ollama API
            self.logger.info(f"🤖 Отправляем запрос в Ollama ({self.model})...")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                self.llm_logger.log_llm_request(formatted_text, "summarization")
            
            summary = await self._call_ollama_api(formatted_text)
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization")
            
            if summary:
                self.logger.info("✅ Суммаризация получена от Ollama")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от Ollama")
                return "❌ Ошибка суммаризации через Ollama"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка суммаризации Ollama: {e}")
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность Ollama
        
        Returns:
            True если Ollama доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Проверяем доступность Ollama сервера
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        
                        # Проверяем, есть ли нужная модель
                        if self.model in models:
                            self.logger.info(f"✅ Ollama доступен, модель {self.model} найдена")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Ollama доступен, но модель {self.model} не найдена. Доступные модели: {models}")
                            return False
                    else:
                        self.logger.error(f"❌ Ollama недоступен, статус: {response.status}")
                        return False
                        
        except aiohttp.ClientError as e:
            self.logger.error(f"❌ Ошибка подключения к Ollama: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Неожиданная ошибка при проверке Ollama: {e}")
            return False
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Генерировать ответ на произвольный промпт
        
        Args:
            prompt: Текст промпта для генерации ответа
            
        Returns:
            Сгенерированный ответ или None при ошибке
        """
        try:
            self.logger.info(f"🤖 Генерируем ответ через Ollama на промпт длиной {len(prompt)} символов")
            self.logger.debug(f"=== GENERATE_RESPONSE INPUT ===")
            self.logger.debug(f"Prompt length: {len(prompt)}")
            self.logger.debug(f"Prompt preview: {prompt[:200]}...")
            self.logger.debug(f"=== END INPUT ===")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                # Определяем тип запроса по содержимому промпта
                request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                self.llm_logger.log_llm_request(prompt, request_type)
            
            response = await self._call_ollama_api(prompt, is_generation=True)
            
            if response:
                self.logger.info(f"✅ Получен ответ от Ollama длиной {len(response)} символов")
                self.logger.debug(f"=== GENERATE_RESPONSE OUTPUT ===")
                self.logger.debug(f"Response length: {len(response)}")
                self.logger.debug(f"Response preview: {response[:200]}...")
                self.logger.debug(f"=== END OUTPUT ===")
                
                # Логируем ответ если логгер установлен
                if self.llm_logger:
                    # Определяем тип ответа по содержимому промпта
                    request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                    self.llm_logger.log_llm_response(response, request_type)
                
                return response
            else:
                self.logger.warning("⚠️ Ollama вернул пустой ответ")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации ответа через Ollama: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере Ollama
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'name': 'Ollama',
            'display_name': 'Ollama (Локальная)',
            'description': f'Локальная модель {self.model} через Ollama',
            'version': self.model,
            'max_tokens': 8000,
            'supports_streaming': True,
            'api_endpoint': self.base_url,
            'provider_type': 'ollama',
            'is_local': True
        }
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации Ollama
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        if not self.base_url:
            self.logger.error("❌ Ollama base URL не настроен")
            return False
        
        if not self.model:
            self.logger.error("❌ Ollama модель не настроена")
            return False
        
        # Проверяем, что URL выглядит корректно
        if not (self.base_url.startswith('http://') or self.base_url.startswith('https://')):
            self.logger.error("❌ Ollama base URL должен начинаться с http:// или https://")
            return False
        
        return True
    
    async def _call_ollama_api(self, text: str, is_generation: bool = False) -> Optional[str]:
        """
        Вызвать Ollama API для суммаризации или генерации
        
        Args:
            text: Текст для обработки
            is_generation: True для генерации, False для суммаризации
            
        Returns:
            Результат обработки или None при ошибке
        """
        try:
            if is_generation:
                # Для генерации используем простой промпт
                prompt = text
            else:
                # Для суммаризации используем централизованный промпт
                from prompts import PromptTemplates
                prompt = PromptTemplates.get_summarization_prompt(text, 'ollama')

            self.logger.info(f"🔗 Отправляем запрос в Ollama")
            self.logger.info(f"📝 Длина текста: {len(text)} символов")
            self.logger.info(f"🤖 Модель: {self.model}")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000 if is_generation else 1000
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'response' in data:
                            result = data['response'].strip()
                            self.logger.info(f"📡 Получен ответ от Ollama: {len(result)} символов")
                            return result
                        else:
                            self.logger.error("❌ Неожиданный формат ответа от Ollama")
                            return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Ошибка Ollama API: {response.status} - {error_text}")
                        return None
                        
        except aiohttp.ClientTimeout:
            self.logger.error(f"❌ Таймаут запроса к Ollama (>{self.timeout}с)")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"❌ Ошибка подключения к Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Ошибка парсинга JSON от Ollama: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Неожиданная ошибка Ollama: {e}")
            return None
