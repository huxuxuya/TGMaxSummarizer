"""
Google Gemini AI провайдер для суммаризации чатов
"""
import os
import google.generativeai as genai
from typing import List, Dict, Optional, Any
from .base_provider import BaseAIProvider

# Подавляем предупреждения ALTS от Google Cloud SDK
import logging
import warnings

# Отключаем предупреждения от Google Cloud SDK
logging.getLogger('google.auth').setLevel(logging.ERROR)
logging.getLogger('google.auth.transport').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=UserWarning, module='google')

class GeminiProvider(BaseAIProvider):
    """Провайдер для работы с Google Gemini API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('GEMINI_API_KEY', '')
        self.model = None
        
        if self.api_key and self.api_key != 'your_gemini_key':
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                self.logger.error(f"❌ Ошибка инициализации Gemini: {e}")
    
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью Gemini
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
        """
        try:
            if not self.model:
                return "❌ Gemini модель не инициализирована"
            
            # Оптимизируем текст
            self.logger.info("🔧 Оптимизируем текст для Gemini...")
            optimized_messages = self.optimize_text(messages)
            
            # Форматируем для анализа
            formatted_text = self.format_messages_for_analysis(optimized_messages)
            
            # Логируем форматированные сообщения (ПОСЛЕ оптимизации)
            if self.llm_logger:
                self.llm_logger.log_formatted_messages(formatted_text, len(optimized_messages))
            
            self.logger.info(f"📊 Статистика для Gemini:")
            self.logger.info(f"   Всего сообщений: {len(messages)}")
            self.logger.info(f"   После оптимизации: {len(optimized_messages)}")
            self.logger.info(f"   Длина текста: {len(formatted_text)} символов")
            
            # Вызываем Gemini API
            self.logger.info("🤖 Отправляем запрос в Gemini...")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                self.llm_logger.log_llm_request(formatted_text, "summarization")
            
            summary = await self._call_gemini_api(formatted_text)
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization")
            
            if summary:
                self.logger.info("✅ Суммаризация получена от Gemini")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от Gemini")
                return "❌ Ошибка суммаризации через Gemini"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка суммаризации Gemini: {e}")
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность Gemini
        
        Returns:
            True если Gemini доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            if not self.model:
                return False
            
            # Простой тест API
            response = self.model.generate_content("Hello")
            return response.text is not None
            
        except Exception as e:
            self.logger.error(f"❌ Gemini недоступен: {e}")
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
            if not self.model:
                self.logger.error("❌ Модель Gemini не инициализирована")
                return None
            
            self.logger.info(f"🤖 Генерируем ответ через Gemini на промпт длиной {len(prompt)} символов")
            self.logger.debug(f"=== GENERATE_RESPONSE INPUT ===")
            self.logger.debug(f"Prompt length: {len(prompt)}")
            self.logger.debug(f"Prompt preview: {prompt[:200]}...")
            self.logger.debug(f"=== END INPUT ===")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                # Определяем тип запроса по содержимому промпта
                request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                self.llm_logger.log_llm_request(prompt, request_type)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2000
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            # Проверяем finish_reason для обработки ошибок безопасности
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                
                if finish_reason == 2:  # SAFETY
                    self.logger.warning("⚠️ Gemini заблокировал ответ из-за политики безопасности")
                    self.logger.debug(f"Safety settings: {candidate.safety_ratings}")
                    return None
                elif finish_reason == 3:  # RECITATION
                    self.logger.warning("⚠️ Gemini заблокировал ответ из-за нарушения авторских прав")
                    return None
                elif finish_reason == 4:  # OTHER
                    self.logger.warning("⚠️ Gemini заблокировал ответ по другим причинам")
                    return None
            
            # Проверяем наличие текста
            if hasattr(response, 'text') and response.text:
                content = response.text
                self.logger.info(f"✅ Получен ответ от Gemini длиной {len(content)} символов")
                self.logger.debug(f"=== GENERATE_RESPONSE OUTPUT ===")
                self.logger.debug(f"Response length: {len(content)}")
                self.logger.debug(f"Response preview: {content[:200]}...")
                self.logger.debug(f"=== END OUTPUT ===")
                
                # Логируем ответ если логгер установлен
                if self.llm_logger:
                    # Определяем тип ответа по содержимому промпта
                    request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                    self.llm_logger.log_llm_response(content, request_type)
                
                return content
            else:
                self.logger.warning("⚠️ Gemini вернул пустой ответ")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации ответа через Gemini: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере Gemini
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'name': 'Gemini',
            'display_name': 'Google Gemini',
            'description': 'Google Gemini 2.5 Flash для суммаризации чатов',
            'version': 'gemini-2.5-flash',
            'max_tokens': 8000,
            'supports_streaming': False,
            'api_endpoint': 'https://generativelanguage.googleapis.com',
            'provider_type': 'gemini'
        }
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации Gemini
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        if not self.api_key or self.api_key == 'your_gemini_key':
            self.logger.error("❌ Gemini API ключ не настроен")
            return False
        
        if len(self.api_key) < 20:
            self.logger.error("❌ Gemini API ключ слишком короткий")
            return False
        
        return True
    
    async def _call_gemini_api(self, text: str) -> Optional[str]:
        """
        Вызвать Gemini API для суммаризации
        
        Args:
            text: Текст для суммаризации
            
        Returns:
            Результат суммаризации или None при ошибке
        """
        try:
            # Используем централизованный промпт
            from prompts import PromptTemplates
            prompt = PromptTemplates.get_summarization_prompt(text[:2000], 'gemini')

            self.logger.info(f"🔗 Отправляем запрос в Gemini")
            self.logger.info(f"📝 Длина текста: {len(text)} символов")
            
            # Простой вызов без дополнительных настроек (как в рабочем скрипте)
            response = self.model.generate_content(prompt)
            
            self.logger.info(f"📡 Получен ответ Gemini")
            
            if response.text:
                return response.text
            else:
                # Проверяем finish_reason
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        if candidate.finish_reason == 2:  # SAFETY
                            self.logger.warning("⚠️ Gemini заблокировал ответ по соображениям безопасности")
                            return "⚠️ Gemini заблокировал запрос по соображениям безопасности. Рекомендуется использовать GigaChat или OpenRouter."
                        elif candidate.finish_reason == 3:  # RECITATION
                            self.logger.warning("⚠️ Gemini заблокировал ответ из-за нарушения авторских прав")
                            return "⚠️ Gemini заблокировал запрос из-за нарушения авторских прав. Рекомендуется использовать GigaChat или OpenRouter."
                        else:
                            self.logger.error(f"❌ Gemini завершил с причиной: {candidate.finish_reason}")
                            return f"❌ Ошибка Gemini: finish_reason = {candidate.finish_reason}"
                
                self.logger.error("❌ Пустой ответ от Gemini")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка запроса к Gemini: {e}")
            return None
    
    async def _try_simple_prompt(self, text: str) -> str:
        """
        Попробовать еще более простой промпт
        """
        try:
            # Максимально простой промпт
            simple_prompt = f"Текст: {text[:500]}"
            
            response = self.model.generate_content(
                simple_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=200
                ),
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            )
            
            if response.text:
                return f"📝 Краткое содержание: {response.text}"
            else:
                return "⚠️ Не удалось обработать текст через Gemini"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка простого промпта: {e}")
            return "⚠️ Ошибка обработки через Gemini"

