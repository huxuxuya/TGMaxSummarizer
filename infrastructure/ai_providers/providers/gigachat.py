"""
GigaChat AI провайдер для суммаризации чатов
"""
import base64
import requests
import urllib3
from typing import List, Dict, Optional, Any
from .base import BaseAIProvider

# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GigaChatProvider(BaseAIProvider):
    """Провайдер для работы с GigaChat API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('GIGACHAT_API_KEY', '')
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.access_token = None
        self.token_expires_at = None
    
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью GigaChat
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
        """
        try:
            # Оптимизируем текст
            self.logger.info("🔧 Оптимизируем текст для GigaChat...")
            optimized_messages = self.optimize_text(messages)
            
            # Форматируем для анализа
            formatted_text = self.format_messages_for_analysis(optimized_messages)
            
            # Логируем форматированные сообщения (ПОСЛЕ оптимизации)
            if self.llm_logger:
                self.llm_logger.log_formatted_messages(formatted_text, len(optimized_messages))
            
            self.logger.info(f"📊 Статистика для GigaChat:")
            self.logger.info(f"   Всего сообщений: {len(messages)}")
            self.logger.info(f"   После оптимизации: {len(optimized_messages)}")
            self.logger.info(f"   Длина текста: {len(formatted_text)} символов")
            
            # Вызываем GigaChat API
            self.logger.info("🤖 Отправляем запрос в GigaChat...")
            
            summary = await self._call_gigachat_api_for_summarization(formatted_text)
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization")
            
            if summary:
                self.logger.info("✅ Суммаризация получена от GigaChat")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от GigaChat")
                return "❌ Ошибка суммаризации через GigaChat"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка суммаризации GigaChat: {e}")
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность GigaChat
        
        Returns:
            True если GigaChat доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            # Пытаемся получить токен доступа
            token = await self._get_access_token()
            return token is not None
        except Exception as e:
            self.logger.error(f"❌ GigaChat недоступен: {e}")
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
            self.logger.info(f"🤖 Генерируем ответ через GigaChat на промпт длиной {len(prompt)} символов")
            self.logger.debug(f"=== GENERATE_RESPONSE INPUT ===")
            self.logger.debug(f"Prompt length: {len(prompt)}")
            self.logger.debug(f"Prompt preview: {prompt[:200]}...")
            self.logger.debug(f"=== END INPUT ===")
            
            # Получаем токен доступа
            token = await self._get_access_token()
            if not token:
                self.logger.error("❌ Не удалось получить токен доступа GigaChat")
                return None
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                # Определяем тип запроса по содержимому промпта
                request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                self.llm_logger.log_llm_request(prompt, request_type)
            
            # Execute API call with provided prompt (NO MODIFICATION!)
            response = await self._execute_api_call(prompt, temperature=0.3, max_tokens=2000)
            
            if response:
                self.logger.info(f"✅ Получен ответ от GigaChat длиной {len(response)} символов")
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
                self.logger.warning("⚠️ GigaChat вернул пустой ответ")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка генерации ответа через GigaChat: {e}")
            return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере GigaChat
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'name': 'GigaChat',
            'display_name': 'GigaChat',
            'description': 'Sberbank GigaChat AI для суммаризации чатов',
            'version': 'latest',
            'max_tokens': 1000,
            'supports_streaming': False,
            'api_endpoint': self.base_url,
            'provider_type': 'gigachat'
        }
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации GigaChat
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        if not self.api_key or self.api_key == 'your_gigachat_key':
            self.logger.error("❌ GigaChat API ключ не настроен")
            return False
        
        if len(self.api_key) < 10:
            self.logger.error("❌ GigaChat API ключ слишком короткий")
            return False
        
        return True
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Получить access token для GigaChat API
        
        Returns:
            Access token или None при ошибке
        """
        # Проверяем, есть ли действующий токен
        if self.access_token and self.token_expires_at:
            from datetime import datetime
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Декодируем API ключ если нужно
        api_key = self.api_key
        if len(api_key) > 50:  # Если это base64
            try:
                api_key = base64.b64decode(api_key).decode('utf-8')
            except:
                pass
        
        # Кодируем ключ для Basic Auth
        auth_string = base64.b64encode(api_key.encode()).decode()
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': '747035d0-e55d-4b35-82cb-a882800f7121',
            'Authorization': f'Basic {auth_string}'
        }
        
        payload = {
            'scope': 'GIGACHAT_API_PERS'
        }
        
        try:
            self.logger.info("🔑 Получаем access token для GigaChat...")
            response = requests.post(
                self.auth_url, 
                headers=headers, 
                data=payload, 
                timeout=30, 
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    self.access_token = result['access_token']
                    # Токен действует 30 минут
                    from datetime import datetime, timedelta
                    self.token_expires_at = datetime.now() + timedelta(minutes=25)
                    self.logger.info("✅ Access token получен для GigaChat")
                    return self.access_token
                else:
                    self.logger.error(f"❌ Нет access_token в ответе GigaChat: {result}")
                    return None
            else:
                self.logger.error(f"❌ Ошибка получения token GigaChat: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка запроса token GigaChat: {e}")
            return None
    
    async def _execute_api_call(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> Optional[str]:
        """
        Execute GigaChat API call with given prompt
        
        Args:
            prompt: Complete prompt to send to API
            temperature: Model temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            API response or None on error
        """
        # Получаем access token
        access_token = await self._get_access_token()
        if not access_token:
            return None
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        data = {
            "model": "GigaChat:latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            self.logger.info(f"🔗 Отправляем запрос на {url}")
            self.logger.info(f"📝 Длина промпта: {len(prompt)} символов")
            self.logger.debug(f"=== EXECUTE_API_CALL INPUT ===")
            self.logger.debug(f"Prompt preview: {prompt[:200]}...")
            self.logger.debug(f"=== END INPUT ===")
            
            response = requests.post(url, headers=headers, json=data, timeout=30, verify=False)
            self.logger.info(f"📡 Получен ответ GigaChat: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                self.logger.info(f"📋 Структура ответа GigaChat: {list(result.keys())}")
                
                if 'choices' in result and len(result['choices']) > 0:
                    api_response = result['choices'][0]['message']['content']
                    self.logger.debug(f"=== EXECUTE_API_CALL OUTPUT ===")
                    self.logger.debug(f"Response length: {len(api_response)}")
                    self.logger.debug(f"Response preview: {api_response[:200]}...")
                    self.logger.debug(f"=== END OUTPUT ===")
                    return api_response
                else:
                    self.logger.error("❌ Неожиданный формат ответа от GigaChat")
                    self.logger.error(f"📋 Полный ответ: {result}")
                    return None
            else:
                self.logger.error(f"❌ HTTP ошибка GigaChat: {response.status_code}")
                self.logger.error(f"📋 Ответ сервера: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("❌ Таймаут запроса к GigaChat")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Ошибка запроса к GigaChat: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Неожиданная ошибка при вызове GigaChat: {e}")
            return None

    async def _call_gigachat_api_for_summarization(self, text: str) -> Optional[str]:
        """
        Create summarization prompt and execute API call
        
        Args:
            text: Formatted messages text
            
        Returns:
            Summarization result or None on error
        """
        # Используем централизованный промпт
        from shared.prompts import PromptTemplates
        prompt = PromptTemplates.get_summarization_prompt(text, 'gigachat')
        
        # Логируем ПОЛНЫЙ промпт (с системным сообщением)
        if self.llm_logger:
            self.llm_logger.log_llm_request(prompt, "summarization")

        # Execute API call with summarization prompt
        return await self._execute_api_call(prompt, temperature=0.7, max_tokens=1000)
