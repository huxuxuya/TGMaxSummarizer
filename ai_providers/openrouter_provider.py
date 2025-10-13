"""
OpenRouter AI провайдер для суммаризации чатов
"""
import httpx
import json
from typing import List, Dict, Optional, Any
from .base_provider import BaseAIProvider

class OpenRouterProvider(BaseAIProvider):
    """Провайдер для работы с OpenRouter API (DeepSeek и другие модели)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('OPENROUTER_API_KEY', '')
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Доступные модели OpenRouter (все 51 бесплатная модель, но показываем только топ 10)
        self.available_models = {
            "alibaba/tongyi-deepresearch-30b-a3b:free": {
                "display_name": "Tongyi DeepResearch 30B A3B (free)",
                "description": "Tongyi DeepResearch is an agentic large language model developed by Tongyi Lab, with 30 billion tota...",
                "free": True,
                "context_length": 131072
            },
            "meituan/longcat-flash-chat:free": {
                "display_name": "Meituan: LongCat Flash Chat (free)",
                "description": "LongCat-Flash-Chat is a large-scale Mixture-of-Experts (MoE) model with 560B total parameters, of wh...",
                "free": True,
                "context_length": 131072
            },
            "nvidia/nemotron-nano-9b-v2:free": {
                "display_name": "NVIDIA: Nemotron Nano 9B V2 (free)",
                "description": "NVIDIA-Nemotron-Nano-9B-v2 is a large language model (LLM) trained from scratch by NVIDIA, and desig...",
                "free": True,
                "context_length": 128000
            },
            "deepseek/deepseek-chat-v3.1:free": {
                "display_name": "DeepSeek: DeepSeek V3.1 (free)",
                "description": "DeepSeek-V3...",
                "free": True,
                "context_length": 163800
            },
            "openai/gpt-oss-20b:free": {
                "display_name": "OpenAI: gpt-oss-20b (free)",
                "description": "gpt-oss-20b is an open-weight 21B parameter model released by OpenAI under the Apache 2...",
                "free": True,
                "context_length": 131072
            },
            "z-ai/glm-4.5-air:free": {
                "display_name": "Z.AI: GLM 4.5 Air (free)",
                "description": "GLM-4...",
                "free": True,
                "context_length": 131072
            },
            "qwen/qwen3-coder:free": {
                "display_name": "Qwen: Qwen3 Coder 480B A35B (free)",
                "description": "Qwen3-Coder-480B-A35B-Instruct is a Mixture-of-Experts (MoE) code generation model developed by the ...",
                "free": True,
                "context_length": 262144
            },
            "moonshotai/kimi-k2:free": {
                "display_name": "MoonshotAI: Kimi K2 0711 (free)",
                "description": "Kimi K2 Instruct is a large-scale Mixture-of-Experts (MoE) language model developed by Moonshot AI, ...",
                "free": True,
                "context_length": 32768
            },
            "cognitivecomputations/dolphin-mistral-24b-venice-edition:free": {
                "display_name": "Venice: Uncensored (free)",
                "description": "Venice Uncensored Dolphin Mistral 24B Venice Edition is a fine-tuned variant of Mistral-Small-24B-In...",
                "free": True,
                "context_length": 32768
            },
            "google/gemma-3n-e2b-it:free": {
                "display_name": "Google: Gemma 3n 2B (free)",
                "description": "Gemma 3n E2B IT is a multimodal, instruction-tuned model developed by Google DeepMind, designed to o...",
                "free": True,
                "context_length": 8192
            },
            "tencent/hunyuan-a13b-instruct:free": {
                "display_name": "Tencent: Hunyuan A13B Instruct (free)",
                "description": "Hunyuan-A13B is a 13B active parameter Mixture-of-Experts (MoE) language model developed by Tencent,...",
                "free": True,
                "context_length": 32768
            },
            "tngtech/deepseek-r1t2-chimera:free": {
                "display_name": "TNG: DeepSeek R1T2 Chimera (free)",
                "description": "DeepSeek-TNG-R1T2-Chimera is the second-generation Chimera model from TNG Tech...",
                "free": True,
                "context_length": 163840
            },
            "mistralai/mistral-small-3.2-24b-instruct:free": {
                "display_name": "Mistral: Mistral Small 3.2 24B (free)",
                "description": "Mistral-Small-3...",
                "free": True,
                "context_length": 131072
            },
            "moonshotai/kimi-dev-72b:free": {
                "display_name": "MoonshotAI: Kimi Dev 72B (free)",
                "description": "Kimi-Dev-72B is an open-source large language model fine-tuned for software engineering and issue re...",
                "free": True,
                "context_length": 131072
            },
            "deepseek/deepseek-r1-0528-qwen3-8b:free": {
                "display_name": "DeepSeek: Deepseek R1 0528 Qwen3 8B (free)",
                "description": "DeepSeek-R1-0528 is a lightly upgraded release of DeepSeek R1 that taps more compute and smarter pos...",
                "free": True,
                "context_length": 131072
            },
            "deepseek/deepseek-r1-0528:free": {
                "display_name": "DeepSeek: R1 0528 (free)",
                "description": "May 28th update to the [original DeepSeek R1](/deepseek/deepseek-r1) Performance on par with [OpenAI...",
                "free": True,
                "context_length": 163840
            },
            "mistralai/devstral-small-2505:free": {
                "display_name": "Mistral: Devstral Small 2505 (free)",
                "description": "Devstral-Small-2505 is a 24B parameter agentic LLM fine-tuned from Mistral-Small-3...",
                "free": True,
                "context_length": 32768
            },
            "google/gemma-3n-e4b-it:free": {
                "display_name": "Google: Gemma 3n 4B (free)",
                "description": "Gemma 3n E4B-it is optimized for efficient execution on mobile and low-resource devices, such as pho...",
                "free": True,
                "context_length": 8192
            },
            "meta-llama/llama-3.3-8b-instruct:free": {
                "display_name": "Meta: Llama 3.3 8B Instruct (free)",
                "description": "A lightweight and ultra-fast variant of Llama 3...",
                "free": True,
                "context_length": 128000
            },
            "qwen/qwen3-4b:free": {
                "display_name": "Qwen: Qwen3 4B (free)",
                "description": "Qwen3-4B is a 4 billion parameter dense language model from the Qwen3 series, designed to support bo...",
                "free": True,
                "context_length": 40960
            },
            "qwen/qwen3-30b-a3b:free": {
                "display_name": "Qwen: Qwen3 30B A3B (free)",
                "description": "Qwen3, the latest generation in the Qwen large language model series, features both dense and mixtur...",
                "free": True,
                "context_length": 40960
            },
            "qwen/qwen3-8b:free": {
                "display_name": "Qwen: Qwen3 8B (free)",
                "description": "Qwen3-8B is a dense 8...",
                "free": True,
                "context_length": 40960
            },
            "qwen/qwen3-14b:free": {
                "display_name": "Qwen: Qwen3 14B (free)",
                "description": "Qwen3-14B is a dense 14...",
                "free": True,
                "context_length": 40960
            },
            "qwen/qwen3-235b-a22b:free": {
                "display_name": "Qwen: Qwen3 235B A22B (free)",
                "description": "Qwen3-235B-A22B is a 235B parameter mixture-of-experts (MoE) model developed by Qwen, activating 22B...",
                "free": True,
                "context_length": 131072
            },
            "tngtech/deepseek-r1t-chimera:free": {
                "display_name": "TNG: DeepSeek R1T Chimera (free)",
                "description": "DeepSeek-R1T-Chimera is created by merging DeepSeek-R1 and DeepSeek-V3 (0324), combining the reasoni...",
                "free": True,
                "context_length": 163840
            },
            "microsoft/mai-ds-r1:free": {
                "display_name": "Microsoft: MAI DS R1 (free)",
                "description": "MAI-DS-R1 is a post-trained variant of DeepSeek-R1 developed by the Microsoft AI team to improve the...",
                "free": True,
                "context_length": 163840
            },
            "shisa-ai/shisa-v2-llama3.3-70b:free": {
                "display_name": "Shisa AI: Shisa V2 Llama 3.3 70B  (free)",
                "description": "Shisa V2 Llama 3...",
                "free": True,
                "context_length": 32768
            },
            "arliai/qwq-32b-arliai-rpr-v1:free": {
                "display_name": "ArliAI: QwQ 32B RpR v1 (free)",
                "description": "QwQ-32B-ArliAI-RpR-v1 is a 32B parameter model fine-tuned from Qwen/QwQ-32B using a curated creative...",
                "free": True,
                "context_length": 32768
            },
            "agentica-org/deepcoder-14b-preview:free": {
                "display_name": "Agentica: Deepcoder 14B Preview (free)",
                "description": "DeepCoder-14B-Preview is a 14B parameter code generation model fine-tuned from DeepSeek-R1-Distill-Q...",
                "free": True,
                "context_length": 96000
            },
            "meta-llama/llama-4-maverick:free": {
                "display_name": "Meta: Llama 4 Maverick (free)",
                "description": "Llama 4 Maverick 17B Instruct (128E) is a high-capacity multimodal language model from Meta, built o...",
                "free": True,
                "context_length": 128000
            },
            "meta-llama/llama-4-scout:free": {
                "display_name": "Meta: Llama 4 Scout (free)",
                "description": "Llama 4 Scout 17B Instruct (16E) is a mixture-of-experts (MoE) language model developed by Meta, act...",
                "free": True,
                "context_length": 128000
            },
            "qwen/qwen2.5-vl-32b-instruct:free": {
                "display_name": "Qwen: Qwen2.5 VL 32B Instruct (free)",
                "description": "Qwen2...",
                "free": True,
                "context_length": 16384
            },
            "deepseek/deepseek-chat-v3-0324:free": {
                "display_name": "DeepSeek: DeepSeek V3 0324 (free)",
                "description": "DeepSeek V3, a 685B-parameter, mixture-of-experts model, is the latest iteration of the flagship cha...",
                "free": True,
                "context_length": 163840
            },
            "mistralai/mistral-small-3.1-24b-instruct:free": {
                "display_name": "Mistral: Mistral Small 3.1 24B (free)",
                "description": "Mistral Small 3...",
                "free": True,
                "context_length": 128000
            },
            "google/gemma-3-4b-it:free": {
                "display_name": "Google: Gemma 3 4B (free)",
                "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs...",
                "free": True,
                "context_length": 32768
            },
            "google/gemma-3-12b-it:free": {
                "display_name": "Google: Gemma 3 12B (free)",
                "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs...",
                "free": True,
                "context_length": 32768
            },
            "google/gemma-3-27b-it:free": {
                "display_name": "Google: Gemma 3 27B (free)",
                "description": "Gemma 3 introduces multimodality, supporting vision-language input and text outputs...",
                "free": True,
                "context_length": 96000
            },
            "nousresearch/deephermes-3-llama-3-8b-preview:free": {
                "display_name": "Nous: DeepHermes 3 Llama 3 8B Preview (free)",
                "description": "DeepHermes 3 Preview is the latest version of our flagship Hermes series of LLMs by Nous Research, a...",
                "free": True,
                "context_length": 131072
            },
            "cognitivecomputations/dolphin3.0-mistral-24b:free": {
                "display_name": "Dolphin3.0 Mistral 24B (free)",
                "description": "Dolphin 3...",
                "free": True,
                "context_length": 32768
            },
            "qwen/qwen2.5-vl-72b-instruct:free": {
                "display_name": "Qwen: Qwen2.5 VL 72B Instruct (free)",
                "description": "Qwen2...",
                "free": True,
                "context_length": 131072
            },
            "mistralai/mistral-small-24b-instruct-2501:free": {
                "display_name": "Mistral: Mistral Small 3 (free)",
                "description": "Mistral Small 3 is a 24B-parameter language model optimized for low-latency performance across commo...",
                "free": True,
                "context_length": 32768
            },
            "deepseek/deepseek-r1-distill-llama-70b:free": {
                "display_name": "DeepSeek: R1 Distill Llama 70B (free)",
                "description": "DeepSeek R1 Distill Llama 70B is a distilled large language model based on [Llama-3...",
                "free": True,
                "context_length": 8192
            },
            "deepseek/deepseek-r1:free": {
                "display_name": "DeepSeek: R1 (free)",
                "description": "DeepSeek R1 is here: Performance on par with [OpenAI o1](/openai/o1), but open-sourced and with full...",
                "free": True,
                "context_length": 163840
            },
            "google/gemini-2.0-flash-exp:free": {
                "display_name": "Google: Gemini 2.0 Flash Experimental (free)",
                "description": "Gemini Flash 2...",
                "free": True,
                "context_length": 1048576
            },
            "meta-llama/llama-3.3-70b-instruct:free": {
                "display_name": "Meta: Llama 3.3 70B Instruct (free)",
                "description": "The Meta Llama 3...",
                "free": True,
                "context_length": 65536
            },
            "qwen/qwen-2.5-coder-32b-instruct:free": {
                "display_name": "Qwen2.5 Coder 32B Instruct (free)",
                "description": "Qwen2...",
                "free": True,
                "context_length": 32768
            },
            "meta-llama/llama-3.2-3b-instruct:free": {
                "display_name": "Meta: Llama 3.2 3B Instruct (free)",
                "description": "Llama 3...",
                "free": True,
                "context_length": 131072
            },
            "qwen/qwen-2.5-72b-instruct:free": {
                "display_name": "Qwen2.5 72B Instruct (free)",
                "description": "Qwen2...",
                "free": True,
                "context_length": 32768
            },
            "mistralai/mistral-nemo:free": {
                "display_name": "Mistral: Mistral Nemo (free)",
                "description": "A 12B parameter model with a 128k token context length built by Mistral in collaboration with NVIDIA...",
                "free": True,
                "context_length": 131072
            },
            "google/gemma-2-9b-it:free": {
                "display_name": "Google: Gemma 2 9B (free)",
                "description": "Gemma 2 9B by Google is an advanced, open-source language model that sets a new standard for efficie...",
                "free": True,
                "context_length": 8192
            },
            "mistralai/mistral-7b-instruct:free": {
                "display_name": "Mistral: Mistral 7B Instruct (free)",
                "description": "A high-performing, industry-standard 7...",
                "free": True,
                "context_length": 32768
            },
        }

        
        # Модель по умолчанию (бесплатная)
        self.default_model = "nvidia/nemotron-nano-9b-v2:free"
        self.current_model = self.default_model
        self.client = None
        
        # Кэш для моделей (TTL: 1 час)
        self._models_cache = None
        self._models_cache_timestamp = 0
        self._models_cache_ttl = 3600  # 1 час в секундах
        
        if self.api_key and self.api_key != 'your_openrouter_key':
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/your-repo",
                    "X-Title": "VK MAX Telegram Bot"
                }
            )
    
    async def initialize(self) -> bool:
        """
        Инициализация OpenRouter провайдера
        
        Returns:
            True если инициализация успешна, False иначе
        """
        try:
            if not self.api_key or self.api_key == 'your_openrouter_key':
                self.logger.error("❌ OpenRouter API ключ не установлен")
                return False
            
            if not self.client:
                self.logger.error("❌ Клиент OpenRouter не создан")
                return False
            
            # Проверяем доступность провайдера
            if not await self.is_available():
                self.logger.error("❌ OpenRouter недоступен")
                return False
            
            self.is_initialized = True
            self.logger.info(f"✅ OpenRouter провайдер успешно инициализирован с моделью: {self.current_model}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации OpenRouter: {e}")
            return False
    
    async def summarize_chat(self, messages: List[Dict], chat_context: Optional[Dict] = None) -> str:
        """
        Суммаризация чата с помощью OpenRouter
        
        Args:
            messages: Список сообщений для суммаризации
            chat_context: Дополнительный контекст чата
            
        Returns:
            Суммаризация в виде строки
        """
        try:
            if not self.client:
                return "❌ OpenRouter клиент не инициализирован"
            
            # Оптимизируем текст
            self.logger.info("🔧 Оптимизируем текст для OpenRouter...")
            optimized_messages = self.optimize_text(messages)
            
            # Форматируем для анализа
            formatted_text = self.format_messages_for_analysis(optimized_messages)
            
            self.logger.info(f"📊 Статистика для OpenRouter:")
            self.logger.info(f"   Всего сообщений: {len(messages)}")
            self.logger.info(f"   После оптимизации: {len(optimized_messages)}")
            self.logger.info(f"   Длина текста: {len(formatted_text)} символов")
            
            # Вызываем OpenRouter API
            self.logger.info("🤖 Отправляем запрос в OpenRouter...")
            
            # Логируем запрос если логгер установлен
            if self.llm_logger:
                self.llm_logger.log_llm_request(formatted_text, "summarization")
            
            summary = await self._call_openrouter_api(formatted_text)
            
            # Логируем ответ если логгер установлен
            if self.llm_logger and summary:
                self.llm_logger.log_llm_response(summary, "summarization")
            
            if summary:
                self.logger.info("✅ Суммаризация получена от OpenRouter")
                return summary
            else:
                self.logger.error("❌ Не удалось получить резюме от OpenRouter")
                return "❌ Ошибка суммаризации через OpenRouter"
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка суммаризации OpenRouter: {e}")
            return f"❌ Ошибка суммаризации: {str(e)}"
    
    async def is_available(self) -> bool:
        """
        Проверить доступность OpenRouter
        
        Returns:
            True если OpenRouter доступен, False иначе
        """
        if not self.validate_config():
            return False
        
        try:
            if not self.client:
                return False
            
            # Простой тест API
            test_data = {
                "model": self.current_model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=test_data
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"❌ OpenRouter недоступен: {e}")
            return False
    
    async def generate_response(self, prompt: str) -> Optional[str]:
        """
        Генерировать ответ на произвольный промпт с retry логикой для 429 ошибок
        
        Args:
            prompt: Текст промпта для генерации ответа
            
        Returns:
            Сгенерированный ответ или None при ошибке
        """
        import asyncio
        
        max_attempts = 4
        delay_seconds = 5
        
        for attempt in range(1, max_attempts + 1):
            try:
                if not self.client:
                    self.logger.error("❌ Клиент OpenRouter не инициализирован")
                    return None
                
                if attempt > 1:
                    self.logger.info(f"🔄 Попытка {attempt}/{max_attempts} после ожидания {delay_seconds}с")
                else:
                    self.logger.info(f"🤖 Генерируем ответ через OpenRouter на промпт длиной {len(prompt)} символов")
                    self.logger.debug(f"=== GENERATE_RESPONSE INPUT ===")
                    self.logger.debug(f"Prompt length: {len(prompt)}")
                    self.logger.debug(f"Prompt preview: {prompt[:200]}...")
                    self.logger.debug(f"=== END INPUT ===")
                    
                    # Логируем запрос если логгер установлен (только на первой попытке)
                    if self.llm_logger:
                        # Определяем тип запроса по содержимому промпта
                        request_type = "reflection" if "рефлексия" in prompt.lower() or "анализ" in prompt.lower() else "improvement"
                        self.llm_logger.log_llm_request(prompt, request_type)
                
                data = {
                    "model": self.current_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
                
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("choices") and result["choices"][0].get("message", {}).get("content"):
                        content = result["choices"][0]["message"]["content"]
                        self.logger.info(f"✅ Получен ответ от OpenRouter длиной {len(content)} символов")
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
                        self.logger.warning("⚠️ OpenRouter вернул пустой ответ")
                        return None
                elif response.status_code == 429:
                    # Rate limit - retry with delay
                    self.logger.warning(f"⚠️ Rate limit (429) - попытка {attempt}/{max_attempts}")
                    if attempt < max_attempts:
                        self.logger.info(f"⏳ Ожидание {delay_seconds} секунд перед повтором...")
                        await asyncio.sleep(delay_seconds)
                        continue  # Retry
                    else:
                        self.logger.error(f"❌ Превышен лимит попыток ({max_attempts}), rate limit не снят")
                        return None
                else:
                    # Other errors - fail immediately
                    self.logger.error(f"❌ OpenRouter вернул ошибку: {response.status_code}")
                    return None
                    
            except Exception as e:
                self.logger.error(f"❌ Ошибка генерации ответа через OpenRouter: {e}")
                return None
        
        return None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Получить информацию о провайдере OpenRouter
        
        Returns:
            Словарь с информацией о провайдере
        """
        return {
            'name': 'OpenRouter',
            'display_name': 'OpenRouter (Multiple Models)',
            'description': 'OpenRouter с множественными моделями для суммаризации чатов',
            'version': self.current_model,
            'current_model': self.current_model,
            'available_models': self.available_models,
            'max_tokens': 4000,
            'supports_streaming': True,
            'api_endpoint': self.base_url,
            'provider_type': 'openrouter'
        }
    
    def validate_config(self) -> bool:
        """
        Валидация конфигурации OpenRouter
        
        Returns:
            True если конфигурация валидна, False иначе
        """
        if not self.api_key or self.api_key == 'your_openrouter_key':
            self.logger.error("❌ OpenRouter API ключ не настроен")
            return False
        
        if len(self.api_key) < 20:
            self.logger.error("❌ OpenRouter API ключ слишком короткий")
            return False
        
        return True
    
    async def _call_openrouter_api(self, text: str) -> Optional[str]:
        """
        Вызвать OpenRouter API для суммаризации
        
        Args:
            text: Текст для суммаризации
            
        Returns:
            Результат суммаризации или None при ошибке
        """
        try:
            prompt = f"""РОЛЬ: Классный руководитель 1 класса, составляет вечернюю сводку для родителей.

ЗАДАЧА: Создай краткую сводку важных событий из родительского чата.

ВКЛЮЧАЙ:
- События с дедлайнами
- Новые правила/требования
- Мероприятия
- Важные объявления
- Ссылки на документы

ИГНОРИРУЙ: координацию встреч, бытовые вопросы, пустые сообщения.

ПРИМЕРЫ ХОРОШИХ ПУНКТОВ:
✅ "Завтра до 10:00 принести справку о здоровье"
✅ "Родительское собрание 15 октября в 18:00"
✅ "Заполнить анкету по ссылке: https://..."

ПРИМЕРЫ ПЛОХИХ ПУНКТОВ:
❌ "Кто-то забирает ребенка"
❌ "Обсуждение обеда"
❌ "Я тоже согласен"

Чат:
{text}

ФОРМАТ:
## 📋 ВАЖНЫЕ СОБЫТИЯ
## 🚨 ТРЕБУЕТСЯ ДЕЙСТВИЙ

ПРАВИЛА: Максимум 3-4 пункта в каждом разделе. Только факты и действия.

ПРАВИЛА ФОРМАТИРОВАНИЯ:
- НЕ используй HTML теги (например <br>, <b>, <i>, <table>)
- НЕ используй Markdown таблицы с символами |
- Используй только простые списки с дефисами (-)
- Используй **жирный текст** для выделения важного
- Используй обычные переносы строк вместо <br>
- Используй ## для заголовков разделов"""

            data = {
                "model": self.current_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            self.logger.info(f"🔗 Отправляем запрос в OpenRouter")
            self.logger.info(f"📝 Длина текста: {len(text)} символов")
            self.logger.info(f"🤖 Модель: {self.current_model}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=data
            )
            
            self.logger.info(f"📡 Получен ответ OpenRouter: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    self.logger.error("❌ Неожиданный формат ответа от OpenRouter")
                    self.logger.error(f"📋 Полный ответ: {result}")
                    return None
            else:
                self.logger.error(f"❌ HTTP ошибка OpenRouter: {response.status_code}")
                self.logger.error(f"📋 Ответ сервера: {response.text}")
                return None
                
        except httpx.TimeoutException:
            self.logger.error("❌ Таймаут запроса к OpenRouter")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.error(f"❌ HTTP ошибка OpenRouter: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Неожиданная ошибка OpenRouter: {e}")
            return None
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    async def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить список доступных моделей (топ 10 лучших бесплатных с OpenRouter API)
        
        Returns:
            Словарь с доступными моделями
        """
        import time
        
        try:
            # Проверяем кэш
            current_time = time.time()
            if (self._models_cache is not None and 
                current_time - self._models_cache_timestamp < self._models_cache_ttl):
                self.logger.info("📋 Используем кэшированный список моделей")
                return self._models_cache
            
            # Получаем актуальный список моделей от OpenRouter API
            api_models = await self._fetch_models_from_api()
            
            if api_models:
                # Выбираем топ 10 лучших бесплатных моделей
                top_10_models = self._select_top_10_free_models(api_models)
                
                # Сохраняем в кэш
                self._models_cache = top_10_models
                self._models_cache_timestamp = current_time
                
                return top_10_models
            else:
                # Fallback к локальному списку, если API недоступен
                self.logger.warning("⚠️ Не удалось получить модели от API, используем локальный список")
                fallback_models = self._get_fallback_models()
                
                # Сохраняем fallback в кэш на короткое время (5 минут)
                self._models_cache = fallback_models
                self._models_cache_timestamp = current_time
                self._models_cache_ttl = 300  # 5 минут для fallback
                
                return fallback_models
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения моделей от API: {e}")
            # Fallback к локальному списку
            fallback_models = self._get_fallback_models()
            
            # Сохраняем fallback в кэш на короткое время
            self._models_cache = fallback_models
            self._models_cache_timestamp = time.time()
            self._models_cache_ttl = 300  # 5 минут для fallback
            
            return fallback_models
    
    async def _fetch_models_from_api(self) -> Optional[List[Dict[str, Any]]]:
        """
        Получить список моделей от OpenRouter API
        
        Returns:
            Список моделей от API или None при ошибке
        """
        try:
            if not self.client:
                self.logger.error("❌ Клиент OpenRouter не инициализирован")
                return None
            
            self.logger.info("🔍 Получаем актуальный список моделей от OpenRouter API...")
            
            response = await self.client.get(f"{self.base_url}/models")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                self.logger.info(f"✅ Получено {len(models)} моделей от OpenRouter API")
                return models
            else:
                self.logger.error(f"❌ OpenRouter API вернул ошибку: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка запроса к OpenRouter API: {e}")
            return None
    
    def _select_top_10_free_models(self, api_models: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Выбрать топ 10 лучших бесплатных моделей из списка API
        
        Args:
            api_models: Список моделей от OpenRouter API
            
        Returns:
            Словарь с топ 10 моделями
        """
        # Фильтруем только бесплатные модели
        free_models = []
        for model in api_models:
            model_id = model.get("id", "")
            pricing = model.get("pricing", {})
            
            # Проверяем, что модель бесплатная
            if pricing.get("prompt") == "0" and pricing.get("completion") == "0":
                # Создаем структуру модели
                model_info = {
                    "display_name": model.get("name", model_id),
                    "description": model.get("description", "Нет описания"),
                    "free": True,
                    "context_length": model.get("context_length", 4096),
                    "pricing": pricing,
                    "top_provider": model.get("top_provider", {}),
                    "per_request_limits": model.get("per_request_limits", {})
                }
                free_models.append((model_id, model_info))
        
        # Сортируем модели по приоритету (размер контекста, популярность и т.д.)
        def model_priority(item):
            model_id, model_info = item
            context_length = model_info.get("context_length", 0)
            
            # Приоритет для известных хороших моделей
            priority_models = {
                "deepseek/deepseek-chat-v3.1:free": 1000,
                "deepseek/deepseek-r1:free": 950,
                "deepseek/deepseek-v3:free": 900,
                "mistral/mistral-small-3.2:free": 850,
                "meta/llama-3.3-8b-instruct:free": 800,
                "qwen/qwen3-8b:free": 750,
                "google/gemma-3-12b:free": 700,
                "moonshotai/kimi-dev-72b:free": 650,
                "microsoft/mai-ds-r1:free": 600,
                "tng/deepseek-r1t-chimera:free": 550
            }
            
            # Если модель в приоритетном списке, используем её приоритет
            if model_id in priority_models:
                return priority_models[model_id]
            
            # Иначе сортируем по размеру контекста
            return context_length
        
        # Сортируем по приоритету (по убыванию)
        free_models.sort(key=model_priority, reverse=True)
        
        # Берем топ 10
        top_10 = free_models[:10]
        
        # Преобразуем в словарь
        result = {}
        for model_id, model_info in top_10:
            result[model_id] = model_info
        
        self.logger.info(f"✅ Выбрано {len(result)} лучших бесплатных моделей")
        return result
    
    def _get_fallback_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить fallback список моделей (локальный)
        
        Returns:
            Словарь с локальными моделями
        """
        # Топ 10 бесплатных моделей OpenRouter (fallback список)
        top_10_free_models = [
            "deepseek/deepseek-chat-v3.1:free",  # Лучшая бесплатная модель
            "deepseek/deepseek-r1:free",  # R1 - отличная для рассуждений
            "deepseek/deepseek-v3:free",  # V3 - флагманская модель
            "mistral/mistral-small-3.2:free",  # Mistral Small 3.2
            "meta/llama-3.3-8b-instruct:free",  # Llama 3.3 8B
            "qwen/qwen3-8b:free",  # Qwen3 8B
            "google/gemma-3-12b:free",  # Gemma 3 12B
            "moonshotai/kimi-dev-72b:free",  # Kimi Dev 72B
            "microsoft/mai-ds-r1:free",  # Microsoft MAI DS R1
            "tng/deepseek-r1t-chimera:free"  # DeepSeek R1T Chimera
        ]
        
        # Фильтруем только топ 10 моделей
        filtered_models = {}
        for model_id in top_10_free_models:
            if model_id in self.available_models:
                filtered_models[model_id] = self.available_models[model_id]
        
        return filtered_models
    
    def clear_models_cache(self):
        """
        Очистить кэш моделей (принудительное обновление)
        """
        self._models_cache = None
        self._models_cache_timestamp = 0
        self.logger.info("🗑️ Кэш моделей очищен")
    
    def set_model(self, model_id: str) -> bool:
        """
        Установить модель для использования
        
        Args:
            model_id: ID модели для установки
            
        Returns:
            True если модель установлена, False если модель не найдена
        """
        # Проверяем модель в полном списке доступных моделей
        if model_id in self.available_models:
            self.current_model = model_id
            self.logger.info(f"✅ Модель OpenRouter изменена на: {model_id}")
            return True
        else:
            # Логируем предупреждение, но все равно устанавливаем модель
            # Это позволяет использовать модели, которые есть в OpenRouter, но не в нашем списке
            self.logger.warning(f"⚠️ Модель {model_id} не найдена в локальном списке, но устанавливаем её")
            self.current_model = model_id
            self.logger.info(f"✅ Модель OpenRouter установлена: {model_id}")
            return True
    
    def get_current_model(self) -> str:
        """
        Получить текущую модель
        
        Returns:
            ID текущей модели
        """
        return self.current_model
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """
        Получить информацию о текущей модели
        
        Returns:
            Информация о текущей модели
        """
        return self.available_models.get(self.current_model, {})
    
    def add_model(self, model_id: str, display_name: str, description: str, free: bool = False) -> bool:
        """
        Добавить новую модель в список доступных
        
        Args:
            model_id: ID модели
            display_name: Отображаемое имя
            description: Описание модели
            free: Бесплатная ли модель
            
        Returns:
            True если модель добавлена
        """
        self.available_models[model_id] = {
            "display_name": display_name,
            "description": description,
            "free": free
        }
        self.logger.info(f"✅ Добавлена новая модель OpenRouter: {model_id}")
        return True
