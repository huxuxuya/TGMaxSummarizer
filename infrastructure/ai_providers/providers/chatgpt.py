"""
ChatGPT AI провайдер для суммаризации чатов
"""
import openai
from typing import List, Dict, Optional, Any
from .base import BaseAIProvider

class ChatGPTProvider(BaseAIProvider):
    """Провайдер для работы с OpenAI ChatGPT API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('OPENAI_API_KEY', '')
        self.client = None
        self.model = "gpt-4"
        
        if self.api_key and self.api_key != 'your_openai_key':
            self.client = openai.OpenAI(api_key=self.api_key)
    
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью ChatGPT
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
        """
        try:
            if not self.client:
                return "❌ ChatGPT клиент не инициализирован"
            
            # Оптимизируем текст
            self.logger.info("🔧 Оптимизируем текст для ChatGPT...")
            optimized_messages = self.optimize_text(messages)
            
            # Форматируем для анализа
            formatted_text = self.format_messages_for_analysis(optimized_messages)
            
            # Логируем форматированные сообщения (ПОСЛЕ оптимизации)
            if self.llm_logger:
                self.llm_logger.log_formatted_messages(formatted_text, len(optimized_messages))
            
            self.logger.info(f"📊 Статистика для ChatGPT:")
            self.logger.info(f"   Всего сообщений: {len(messages)}")
            self.logger.info(f"   После оптимизации: {len(optimized_messages)}")
            self.logger.info(f"   Длина текста: {len(formatted_text)} символов")
            
            # Вызываем ChatGPT API
            self.logger.info("🤖 Отправляем запрос в ChatGPT...")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                self.llm_logger.log_llm_request(formatted_text, "summarization")
            
            summary = await self._call_chatgpt_api(formatted_text)
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization")
            
            if summary:
                self.logger.info("✅ Суммаризация получена от ChatGPT")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от ChatGPT")
                return "❌ Ошибка суммаризации через ChatGPT"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка суммаризации ChatGPT: {e}")
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность ChatGPT
        
        Returns:
            True если ChatGPT доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            if not self.client:
                return False
            
            # Простой тест API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return response.choices[0].message.content is not None
            
        except Exception as e:
            self.logger.error(f"❌ ChatGPT недоступен: {e}")
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
            if not self.client:
                self.logger.error("❌ Клиент ChatGPT не инициализирован")
                return None
            
            self.logger.info(f"🤖 Генерируем ответ через ChatGPT на промпт длиной {len(prompt)} символов")
            self.logger.debug(f"=== GENERATE_RESPONSE INPUT ===")
            self.logger.debug(f"Prompt length: {len(prompt)}")
            self.logger.debug(f"Prompt preview: {prompt[:200]}...")
            self.logger.debug(f"=== END INPUT ===")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                # Определяем тип запроса по содержимому промпта
                request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                self.llm_logger.log_llm_request(prompt, request_type)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            if response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content
                self.logger.info(f"✅ Получен ответ от ChatGPT длиной {len(content)} символов")
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
                self.logger.warning("⚠️ ChatGPT вернул пустой ответ")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации ответа через ChatGPT: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере ChatGPT
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'name': 'ChatGPT',
            'display_name': 'ChatGPT',
            'description': 'OpenAI ChatGPT для суммаризации чатов',
            'version': self.model,
            'max_tokens': 4000,
            'supports_streaming': True,
            'api_endpoint': 'https://api.openai.com/v1',
            'provider_type': 'chatgpt'
        }
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации ChatGPT
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        if not self.api_key or self.api_key == 'your_openai_key':
            self.logger.error("❌ ChatGPT API ключ не настроен")
            return False
        
        if len(self.api_key) < 20:
            self.logger.error("❌ ChatGPT API ключ слишком короткий")
            return False
        
        if not self.api_key.startswith('sk-'):
            self.logger.warning("⚠️ ChatGPT API ключ не начинается с 'sk-'")
        
        return True
    
    async def _call_chatgpt_api(self, text: str) -> Optional[str]:
        """
        Вызвать ChatGPT API для суммаризации
        
        Args:
            text: Текст для суммаризации
            
        Returns:
            Результат суммаризации или None при ошибке
        """
        try:
            # Используем централизованный промпт
            from prompts import PromptTemplates
            prompt = PromptTemplates.get_summarization_prompt(text, 'chatgpt')

            self.logger.info(f"🔗 Отправляем запрос в ChatGPT")
            self.logger.info(f"📝 Длина текста: {len(text)} символов")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            self.logger.info(f"📡 Получен ответ ChatGPT: {response.usage.total_tokens} токенов")
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                self.logger.error("❌ Неожиданный формат ответа от ChatGPT")
                return None
                
        except openai.RateLimitError as e:
            self.logger.error(f"❌ Превышен лимит запросов ChatGPT: {e}")
            return None
        except openai.AuthenticationError as e:
            self.logger.error(f"❌ Ошибка аутентификации ChatGPT: {e}")
            return None
        except openai.APIError as e:
            self.logger.error(f"❌ Ошибка API ChatGPT: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Неожиданная ошибка ChatGPT: {e}")
            return None
