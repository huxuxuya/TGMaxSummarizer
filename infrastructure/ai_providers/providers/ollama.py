"""
Ollama AI провайдер для локальных моделей
"""
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional, Any
from .base import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    """Провайдер для работы с локальными моделями через Ollama API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config.get('model', 'deepseek-r1:8b')
        self.timeout = config.get('timeout', 600)  # Таймаут для Ollama запросов (10 минут)
        
        # Отладочная информация
        self.logger.info(f"🔗 DEBUG: OllamaProvider инициализирован с base_url = {self.base_url}")
        self.logger.info(f"🔗 DEBUG: OllamaProvider инициализирован с model = {self.model}")
    
    def set_model(self, model_name: str):
        """
        Установить модель для использования
        
        Args:
            model_name: Название модели (например, 'gemma3:12b')
        """
        print(f"🔍 DEBUG: OllamaProvider.set_model вызван с model_name: {model_name}")
        self.logger.info(f"🔍 DEBUG: OllamaProvider.set_model вызван с model_name: {model_name}")
        
        self.model = model_name
        print(f"🔍 DEBUG: OllamaProvider.model установлен в: {self.model}")
        self.logger.info(f"🔍 DEBUG: OllamaProvider.model установлен в: {self.model}")
        self.logger.info(f"🔗 Модель Ollama изменена на: {model_name}")
        
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
            
            import time
            start_time = time.time()
            summary = await self._call_ollama_api(formatted_text)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization", response_time)
                self.llm_logger.log_stage_time('summarization', response_time)
            
            if summary:
                self.logger.info("✅ Суммаризация получена от Ollama")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от Ollama")
                return "❌ Ошибка суммаризации через Ollama"
                
        except Exception as e:
            error_msg = f"❌ Ошибка суммаризации Ollama: {e}"
            self.logger.error(error_msg)
            # Логируем ошибку если есть логгер
            if self.llm_logger:
                self.llm_logger.log_error("summarization", error_msg, str(e))
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность Ollama
        
        Returns:
            True если Ollama сервер доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            self.logger.info(f"🔗 DEBUG: Проверяем доступность Ollama по URL: {self.base_url}/api/tags")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                # Проверяем доступность Ollama сервера
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model['name'] for model in data.get('models', [])]
                        
                        # Для Ollama достаточно, что сервер доступен и есть хотя бы одна модель
                        if models:
                            self.logger.info(f"✅ Ollama доступен, найдено {len(models)} моделей")
                            # Проверяем, есть ли нужная модель (для информации)
                            if self.model in models:
                                self.logger.info(f"✅ Модель по умолчанию {self.model} найдена")
                            else:
                                self.logger.info(f"ℹ️ Модель по умолчанию {self.model} не найдена, но есть другие модели")
                            return True
                        else:
                            self.logger.warning(f"⚠️ Ollama доступен, но нет установленных моделей")
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
    
    async def generate_response(self, prompt: str, stream_callback=None) -> Optional[str]:
        """
        Генерировать ответ на произвольный промпт
        
        Args:
            prompt: Текст промпта для генерации ответа
            stream_callback: Функция для обработки потоковых данных (text_chunk)
            
        Returns:
            Сгенерированный ответ или None при ошибке
        """
        try:
            import time
            start_time = time.time()
            
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
            
            response = await self._call_ollama_api(prompt, is_generation=True, stream_callback=stream_callback)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response:
                self.logger.info(f"✅ Получен ответ от Ollama длиной {len(response)} символов за {response_time:.2f}с")
                self.logger.debug(f"=== GENERATE_RESPONSE OUTPUT ===")
                self.logger.debug(f"Response length: {len(response)}")
                self.logger.debug(f"Response preview: {response[:200]}...")
                self.logger.debug(f"=== END OUTPUT ===")
                
                # Логируем ответ если логгер установлен
                if self.llm_logger:
                    # Определяем тип ответа по содержимому промпта
                    request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                    self.llm_logger.log_llm_response(response, request_type, response_time)
                    
                    # Записываем время выполнения этапа
                    if request_type == "reflection":
                        self.llm_logger.log_stage_time('reflection', response_time)
                    elif request_type == "improvement":
                        self.llm_logger.log_stage_time('improvement', response_time)
                
                return response
            else:
                self.logger.warning("⚠️ Ollama вернул пустой ответ")
                return None
                
        except Exception as e:
            error_msg = f"❌ Ошибка генерации ответа через Ollama: {e}"
            self.logger.error(error_msg)
            # Логируем ошибку если есть логгер
            if self.llm_logger:
                # Определяем тип запроса по содержимому промпта
                request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                self.llm_logger.log_error(request_type, error_msg, str(e))
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
    
    async def _call_ollama_api(self, text: str, is_generation: bool = False, stream_callback=None) -> Optional[str]:
        """
        Вызвать Ollama API для суммаризации или генерации
        
        Args:
            text: Текст для обработки
            is_generation: True для генерации, False для суммаризации
            stream_callback: Функция для обработки потоковых данных (text_chunk)
            
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
            self.logger.info(f"🔗 DEBUG: URL для запроса: {self.base_url}/api/generate")
            self.logger.info(f"📝 Длина текста: {len(text)} символов")
            self.logger.info(f"🤖 Модель: {self.model}")
            
            # Используем streaming если есть callback
            use_streaming = stream_callback is not None
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": use_streaming,
                "options": {
                    "temperature": 0.7
                }
            }
            
            self.logger.info(f"🔗 DEBUG: Отправляем POST запрос с таймаутом {self.timeout}с")
            self.logger.info(f"🔗 DEBUG: Payload: {payload}")
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                self.logger.info(f"🔗 DEBUG: Создана сессия, отправляем запрос...")
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    self.logger.info(f"🔗 DEBUG: Получен ответ со статусом {response.status}")
                    
                    if response.status == 200:
                        if use_streaming:
                            # Обработка потокового ответа
                            full_response = ""
                            async for line in response.content:
                                line_str = line.decode('utf-8').strip()
                                if line_str:
                                    try:
                                        chunk_data = json.loads(line_str)
                                        if 'response' in chunk_data:
                                            chunk_text = chunk_data['response']
                                            full_response += chunk_text
                                            
                                            # Вызываем callback для анимации
                                            if stream_callback:
                                                stream_callback(chunk_text)
                                            
                                            # Проверяем завершение
                                            if chunk_data.get('done', False):
                                                break
                                    except json.JSONDecodeError:
                                        # Пропускаем некорректные JSON строки
                                        continue
                            
                            result = full_response.strip()
                            self.logger.info(f"📡 Получен потоковый ответ от Ollama: {len(result)} символов")
                            return result
                        else:
                            # Обычная обработка (не streaming)
                            data = await response.json()
                            self.logger.info(f"🔗 DEBUG: Получен JSON ответ от Ollama: {data}")
                            
                            if 'response' in data:
                                result = data['response'].strip()
                                self.logger.info(f"📡 Получен ответ от Ollama: {len(result)} символов")
                                return result
                            else:
                                self.logger.error("❌ Неожиданный формат ответа от Ollama")
                                self.logger.error(f"🔗 DEBUG: Ключи в ответе: {list(data.keys())}")
                                return None
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Ошибка Ollama API: {response.status} - {error_text}")
                        self.logger.error(f"🔗 DEBUG: Полный ответ сервера: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            error_msg = f"❌ Таймаут запроса к Ollama (>{self.timeout}с)"
            self.logger.error(error_msg)
            # Логируем ошибку если есть логгер
            if self.llm_logger:
                self.llm_logger.log_error("extraction", error_msg, None)
            return None
        except aiohttp.ClientError as e:
            error_msg = f"❌ Ошибка подключения к Ollama: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔗 DEBUG: Тип ошибки: {type(e)}")
            # Логируем ошибку
            if self.llm_logger:
                self.llm_logger.log_error("extraction", error_msg, str(e))
            return None
        except json.JSONDecodeError as e:
            error_msg = f"❌ Ошибка парсинга JSON от Ollama: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔗 DEBUG: Тип ошибки: {type(e)}")
            # Логируем ошибку
            if self.llm_logger:
                self.llm_logger.log_error("extraction", error_msg, str(e))
            return None
        except Exception as e:
            error_msg = f"❌ Неожиданная ошибка Ollama: {e}"
            self.logger.error(error_msg)
            self.logger.error(f"🔗 DEBUG: Тип ошибки: {type(e)}")
            self.logger.error(f"🔗 DEBUG: Аргументы ошибки: {e.args}")
            # Логируем ошибку
            if self.llm_logger:
                self.llm_logger.log_error("extraction", error_msg, str(e))
            return None
    
    async def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить список доступных моделей Ollama
        
        Returns:
            Словарь с информацией о моделях
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = {}
                        
                        if 'models' in data:
                            for model_info in data['models']:
                                model_name = model_info.get('name', '')
                                if model_name:
                                    # Создаем отображаемое имя
                                    display_name = model_name.replace(':', ' ').title()
                                    
                                    models[model_name] = {
                                        'display_name': display_name,
                                        'name': model_name,
                                        'size': model_info.get('size', 0),
                                        'modified_at': model_info.get('modified_at', ''),
                                        'free': True  # Локальные модели всегда бесплатные
                                    }
                        
                        self.logger.info(f"✅ Получено {len(models)} моделей Ollama")
                        return models
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Ошибка получения моделей Ollama: {response.status} - {error_text}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения моделей Ollama: {e}")
            return {}
