"""
Анализ чатов с помощью модульной системы AI провайдеров
"""
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

from ai_providers import ProviderFactory
from config import AI_PROVIDERS, DEFAULT_AI_PROVIDER, FALLBACK_PROVIDERS, ENABLE_REFLECTION, AUTO_IMPROVE_SUMMARY, ENABLE_LLM_LOGGING, LLM_LOGS_DIR
from telegram_formatter import TelegramFormatter
from llm_logger import LLMLogger
from prompts import PromptTemplates

logger = logging.getLogger(__name__)

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы Markdown для Telegram (совместимость)
    
    Args:
        text: Текст для экранирования
        
    Returns:
        Экранированный текст (теперь просто возвращает исходный текст)
    """
    # Не экранируем здесь - это сделает TelegramMessageSender
    return text

class ChatAnalyzer:
    """Класс для анализа чатов с помощью модульной системы AI провайдеров"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация анализатора чатов
        
        Args:
            config: Конфигурация провайдеров (по умолчанию из config.py)
        """
        # Преобразуем конфигурацию в формат, ожидаемый провайдерами
        if config is None or isinstance(config, str):
            # Создаем конфигурацию из AI_PROVIDERS
            self.config = {}
            for provider_name, provider_config in AI_PROVIDERS.items():
                if provider_name == 'gigachat':
                    self.config['GIGACHAT_API_KEY'] = provider_config.get('api_key', '')
                elif provider_name == 'chatgpt':
                    self.config['OPENAI_API_KEY'] = provider_config.get('api_key', '')
                elif provider_name == 'openrouter':
                    self.config['OPENROUTER_API_KEY'] = provider_config.get('api_key', '')
                elif provider_name == 'gemini':
                    self.config['GEMINI_API_KEY'] = provider_config.get('api_key', '')
        else:
            self.config = config
            
        self.provider_factory = ProviderFactory()
        self.current_provider = None
        self.provider_history = []
        
        logger.info("✅ ChatAnalyzer инициализирован с модульной архитектурой")
        logger.debug(f"🔍 Конфигурация ChatAnalyzer: {self.config}")
    
    async def analyze_chat_by_date(self, messages: List[Dict], provider_name: Optional[str] = None, chat_context: Optional[Dict] = None) -> Optional[str]:
        """
        Анализировать чат за определенную дату с помощью выбранного провайдера
        
        Args:
            messages: Список сообщений для анализа
            provider_name: Имя провайдера (если None, используется лучший доступный)
            chat_context: Дополнительный контекст чата
            
        Returns:
            Результат анализа или None при ошибке
        """
        try:
            # Выбираем провайдера
            if provider_name:
                provider = self.provider_factory.create_provider(provider_name, self.config)
                if not provider:
                    logger.error(f"❌ Не удалось создать провайдер: {provider_name}")
                    return None
            else:
                # Используем лучший доступный провайдер
                best_provider_name = await self.provider_factory.get_best_available_provider(
                    self.config, 
                    DEFAULT_AI_PROVIDER
                )
                if not best_provider_name:
                    logger.error("❌ Нет доступных AI провайдеров")
                    return None
                
                provider = self.provider_factory.create_provider(best_provider_name, self.config)
                provider_name = best_provider_name
            
            # Инициализируем провайдера
            if not await provider.initialize():
                logger.error(f"❌ Не удалось инициализировать провайдер: {provider_name}")
                
                # Пробуем fallback провайдеров
                for fallback_name in FALLBACK_PROVIDERS:
                    if fallback_name != provider_name:
                        logger.info(f"🔄 Пробуем fallback провайдер: {fallback_name}")
                        fallback_provider = self.provider_factory.create_provider(fallback_name, self.config)
                        if fallback_provider and await fallback_provider.initialize():
                            provider = fallback_provider
                            provider_name = fallback_name
                            break
                else:
                    logger.error("❌ Все провайдеры недоступны")
                    return None
            
            # Если это OpenRouter, устанавливаем выбранную пользователем модель
            # (только для функций с user_id параметром)
            
            self.current_provider = provider
            self.provider_history.append({
                'provider': provider_name,
                'timestamp': datetime.now(),
                'messages_count': len(messages)
            })
            
            logger.info(f"🤖 Используем провайдер: {provider.get_display_name()}")
            
            # Выполняем суммаризацию
            summary = await provider.summarize_chat(messages, chat_context)
            
            if summary:
                logger.info(f"✅ Суммаризация получена от {provider.get_display_name()}")
                return summary
            else:
                logger.error(f"❌ Не удалось получить суммаризацию от {provider.get_display_name()}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа чата: {e}")
            return None
    
    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Получить список доступных провайдеров (с проверкой доступности)
        
        Returns:
            Список доступных провайдеров с информацией
        """
        try:
            available_providers = []
            
            for provider_name in self.provider_factory.get_available_providers():
                provider = self.provider_factory.create_provider(provider_name, self.config)
                if provider:
                    is_available = await provider.is_available()
                    provider_info = provider.get_provider_info()
                    provider_info['available'] = is_available
                    provider_info['name'] = provider_name
                    available_providers.append(provider_info)
            
            return available_providers
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка провайдеров: {e}")
            return []
    
    def get_providers_with_saved_status(self, db_manager=None) -> List[Dict[str, Any]]:
        """
        Получить список провайдеров с сохраненным статусом (без проверки доступности)
        
        Args:
            db_manager: Объект базы данных для получения сохраненного статуса
        
        Returns:
            Список провайдеров с информацией из сохраненного статуса
        """
        try:
            providers = []
            
            for provider_name in self.provider_factory.get_available_providers():
                provider = self.provider_factory.create_provider(provider_name, self.config)
                if provider:
                    provider_info = provider.get_provider_info()
                    provider_info['name'] = provider_name
                    
                    # Получаем сохраненный статус из базы данных
                    if db_manager:
                        availability_stats = db_manager.get_provider_availability(provider_name)
                        if availability_stats:
                            provider_info['available'] = availability_stats.get('is_available', False)
                        else:
                            # Если нет информации в БД, считаем провайдер недоступным (требует проверки)
                            provider_info['available'] = False
                    else:
                        # Если нет доступа к БД, считаем провайдер недоступным
                        provider_info['available'] = False
                    
                    providers.append(provider_info)
            
            return providers
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка провайдеров: {e}")
            return []
    
    async def validate_provider(self, provider_name: str) -> bool:
        """
        Валидировать конкретный провайдер
        
        Args:
            provider_name: Имя провайдера для валидации
            
        Returns:
            True если провайдер валиден и доступен, False иначе
        """
        try:
            provider = self.provider_factory.create_provider(provider_name, self.config)
            if not provider:
                return False
            
            return await provider.is_available()
            
        except Exception as e:
            logger.error(f"❌ Ошибка валидации провайдера {provider_name}: {e}")
            return False
    
    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о провайдере
        
        Args:
            provider_name: Имя провайдера
            
        Returns:
            Информация о провайдере или None
        """
        return self.provider_factory.get_provider_info(provider_name, self.config)
    
    def get_current_provider(self) -> Optional[str]:
        """
        Получить имя текущего провайдера
        
        Returns:
            Имя текущего провайдера или None
        """
        return self.current_provider.get_name() if self.current_provider else None
    
    def get_provider_history(self) -> List[Dict[str, Any]]:
        """
        Получить историю использования провайдеров
        
        Returns:
            Список с историей использования провайдеров
        """
        return self.provider_history.copy()
    
    async def test_all_providers(self) -> Dict[str, bool]:
        """
        Протестировать все провайдеры
        
        Returns:
            Словарь с результатами тестирования
        """
        try:
            results = {}
            
            for provider_name in self.provider_factory.get_available_providers():
                logger.info(f"🧪 Тестируем провайдер: {provider_name}")
                is_available = await self.validate_provider(provider_name)
                results[provider_name] = is_available
                
                status = "✅ Доступен" if is_available else "❌ Недоступен"
                logger.info(f"   {status}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка тестирования провайдеров: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получить статистику использования анализатора
        
        Returns:
            Словарь со статистикой
        """
        total_analyses = len(self.provider_history)
        
        if total_analyses == 0:
            return {
                'total_analyses': 0,
                'providers_used': {},
                'current_provider': None
            }
        
        # Подсчитываем использование провайдеров
        providers_used = {}
        for entry in self.provider_history:
            provider = entry['provider']
            providers_used[provider] = providers_used.get(provider, 0) + 1
        
        return {
            'total_analyses': total_analyses,
            'providers_used': providers_used,
            'current_provider': self.get_current_provider(),
            'last_analysis': self.provider_history[-1] if self.provider_history else None
        }
    
    # Backward compatibility methods
    def optimize_text(self, messages: List[Dict]) -> List[Dict]:
        """
        Оптимизировать текст чата (backward compatibility)
        
        Args:
            messages: Список сообщений
            
        Returns:
            Оптимизированный список сообщений
        """
        if self.current_provider:
            return self.current_provider.optimize_text(messages)
        else:
            # Fallback к базовой реализации
            import re
            optimized_messages = []
            
            for msg in messages:
                text = msg.get('text', '').strip()
                if not text:
                    continue
                    
                # Убираем лишние символы и сокращаем
                text = re.sub(r'\s+', ' ', text)
                
                if len(text) > 200:
                    text = text[:200] + "..."
                
                sender_name = msg.get('sender_name', 'Неизвестно')
                time = msg.get('message_time', 0)
                
                if time:
                    try:
                        dt = datetime.fromtimestamp(time / 1000)
                        time_str = dt.strftime('%H:%M')
                    except (ValueError, OSError):
                        time_str = "??:??"
                else:
                    time_str = "??:??"
                
                optimized_messages.append({
                    'time': time_str,
                    'sender': sender_name,
                    'text': text
                })
            
            return optimized_messages
    
    def format_chat_for_analysis(self, messages: List[Dict]) -> str:
        """
        Форматировать чат для анализа (backward compatibility)
        
        Args:
            messages: Список сообщений
            
        Returns:
            Отформатированная строка
        """
        if self.current_provider:
            return self.current_provider.format_messages_for_analysis(messages)
        else:
            # Fallback к базовой реализации
            formatted_lines = []
            
            for msg in messages:
                time_str = msg.get('time', '??:??')
                sender = msg.get('sender', 'Неизвестно')
                text = msg.get('text', '')
                
                if text.strip():
                    line = f"[{time_str}] {sender}: {text}"
                    formatted_lines.append(line)
            
            full_text = "\n".join(formatted_lines)
            
            max_length = 8000
            if len(full_text) > max_length:
                full_text = full_text[:max_length] + "\n... (текст обрезан для экономии токенов)"
            
            return full_text
    
    async def analyze_chat_with_specific_model(self, messages: List[Dict], provider_name: str, model_id: str = None, user_id: int = None) -> Optional[str]:
        """
        Анализ чата с конкретной моделью (для выбора модели при анализе)
        
        Args:
            messages: Список сообщений для анализа
            provider_name: Название провайдера
            model_id: ID модели (для OpenRouter)
            user_id: ID пользователя
            
        Returns:
            Суммаризация или None при ошибке
        """
        try:
            logger.info(f"🤖 Анализ с конкретной моделью: {provider_name}")
            if model_id:
                logger.info(f"🔗 Модель: {model_id}")
            
            # Создаем LLM логгер если включено логирование
            llm_logger = None
            if ENABLE_LLM_LOGGING:
                # Определяем дату из сообщений
                date = None
                if messages and len(messages) > 0:
                    # Пытаемся извлечь дату из первого сообщения
                    first_msg = messages[0]
                    if 'date' in first_msg:
                        date = first_msg['date']
                    elif 'message_time' in first_msg:
                        # Конвертируем timestamp в дату
                        from datetime import datetime
                        try:
                            dt = datetime.fromtimestamp(first_msg['message_time'] / 1000)
                            date = dt.strftime('%Y-%m-%d')
                        except (ValueError, OSError):
                            pass
                
                llm_logger = LLMLogger(LLM_LOGS_DIR, date=date)
                llm_logger.clear_date_logs()  # Очищаем старые логи для этой даты
                llm_logger.set_session_info(provider_name, model_id, None, user_id)
                logger.info(f"📁 LLM Logger создан: {llm_logger.get_logs_path()}")
            
            # Создаем провайдера
            provider = self.provider_factory.create_provider(provider_name, self.config)
            if not provider:
                logger.error(f"❌ Не удалось создать провайдер: {provider_name}")
                return None
            
            # Устанавливаем логгер в провайдер
            if llm_logger:
                provider.set_llm_logger(llm_logger)
            
            # Инициализируем провайдера
            if not await provider.initialize():
                logger.error(f"❌ Не удалось инициализировать провайдер: {provider_name}")
                return None
            
            # Если это OpenRouter и указана модель, устанавливаем её
            if provider_name == 'openrouter' and model_id and hasattr(provider, 'set_model'):
                provider.set_model(model_id)
                logger.info(f"🔗 Установлена модель OpenRouter: {model_id}")
            
            # Оптимизация и логирование теперь происходит в провайдерах
            
            # Создаем контекст чата
            chat_context = {
                'total_messages': len(messages),
                'date': messages[0].get('message_time', 0) if messages else 0,
                'provider': provider_name,
                'model': model_id
            }
            
            # Выполняем суммаризацию
            summary = await provider.summarize_chat(messages, chat_context)
            
            # Проверяем успешность суммаризации - если не получилось, прерываем
            if not summary:
                logger.error(f"❌ Не удалось получить суммаризацию от {provider_name}")
                logger.warning("⚠️ Прерываем процесс - рефлексия и улучшение не будут выполнены")
                
                # Логируем неудачную попытку
                if llm_logger:
                    llm_logger.log_session_summary({
                        'summary': None,
                        'reflection': None,
                        'improved': None,
                        'error': 'Суммаризация не выполнена'
                    })
                
                return None
            
            # Суммаризация успешна, продолжаем
            if summary:
                logger.info(f"✅ Суммаризация получена от {provider_name}")
                if model_id:
                    logger.info(f"🔗 Использована модель: {model_id}")
                
                # Выполняем рефлексию для улучшения суммаризации (если включена)
                logger.debug(f"=== REFLECTION CHECK ===")
                logger.debug(f"ENABLE_REFLECTION value: {ENABLE_REFLECTION}")
                logger.debug(f"ENABLE_REFLECTION type: {type(ENABLE_REFLECTION)}")
                
                if ENABLE_REFLECTION:
                    logger.debug("=== REFLECTION ENABLED ===")
                    logger.debug(f"Provider: {provider}")
                    logger.debug(f"Summary: {summary[:100]}...")
                    logger.debug(f"Messages count: {len(messages)}")
                    logger.debug(f"Chat context: {chat_context}")
                    
                    reflection = await self.perform_reflection(provider, summary, messages, chat_context, llm_logger)
                    logger.debug(f"Reflection result: {reflection}")
                    
                    # Проверяем успешность рефлексии
                    if not reflection:
                        logger.warning("⚠️ Рефлексия не выполнена, возвращаем исходную суммаризацию")
                        logger.warning("⚠️ Прерываем процесс - улучшение суммаризации не будет выполнено")
                        logger.debug("=== REFLECTION FAILED ===")
                        result = {
                            'summary': summary,
                            'reflection': None,
                            'improved': None,
                            'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n*❌ Ошибка:* Рефлексия не была выполнена",
                            'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n*❌ Ошибка:* Рефлексия не была выполнена"
                        }
                        
                        # Логируем результаты
                        if llm_logger:
                            llm_logger.log_raw_result(summary)
                            llm_logger.log_formatted_result(result['display_text'])
                            llm_logger.log_session_summary(result)
                        
                        return result
                    
                    # Рефлексия успешна, продолжаем
                    if reflection:
                        logger.info("🔄 Рефлексия выполнена успешно")
                        logger.debug(f"Reflection text: {reflection[:200]}...")
                        
                        # Не экранируем здесь - это сделает TelegramMessageSender
                        escaped_reflection = reflection
                        
                        # Автоматически улучшаем суммаризацию, если включено
                        if AUTO_IMPROVE_SUMMARY:
                            improved_summary = await self.improve_summary_with_reflection(
                                provider, summary, reflection, messages, chat_context, llm_logger
                            )
                            if improved_summary:
                                logger.info("✨ Суммаризация автоматически улучшена")
                                escaped_improved = improved_summary
                                # Возвращаем структурированный результат с сворачиваемым текстом
                                result = {
                                    'summary': summary,
                                    'reflection': reflection,
                                    'improved': improved_summary,
                                    'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n> 🤔 *Рефлексия и анализ*\n> {escaped_reflection}\n\n> ✨ *Улучшенная суммаризация*\n> {escaped_improved}",
                                    'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n||🤔 Рефлексия и анализ:||\n||{escaped_reflection}||\n\n||✨ Улучшенная суммаризация:||\n||{escaped_improved}||"
                                }
                                
                                # Логируем результаты
                                if llm_logger:
                                    llm_logger.log_raw_result(summary)
                                    llm_logger.log_formatted_result(result['display_text'])
                                    llm_logger.log_session_summary(result)
                                
                                return result
                            else:
                                logger.warning("⚠️ Не удалось улучшить суммаризацию, показываем с рефлексией")
                                result = {
                                    'summary': summary,
                                    'reflection': reflection,
                                    'improved': None,
                                    'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n> 🤔 *Рефлексия и улучшения*\n> {escaped_reflection}",
                                    'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n||🤔 Рефлексия и улучшения:||\n||{escaped_reflection}||"
                                }
                                
                                # Логируем результаты
                                if llm_logger:
                                    llm_logger.log_raw_result(summary)
                                    llm_logger.log_formatted_result(result['display_text'])
                                    llm_logger.log_session_summary(result)
                                
                                return result
                        else:
                            result = {
                                'summary': summary,
                                'reflection': reflection,
                                'improved': None,
                                'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n> 🤔 *Рефлексия и улучшения*\n> {escaped_reflection}",
                                'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n||🤔 Рефлексия и улучшения:||\n||{escaped_reflection}||"
                            }
                            
                            # Логируем результаты
                            if llm_logger:
                                llm_logger.log_raw_result(summary)
                                llm_logger.log_formatted_result(result['display_text'])
                                llm_logger.log_session_summary(result)
                            
                            return result
                else:
                    logger.info("ℹ️ Рефлексия отключена в настройках")
                    logger.debug("=== REFLECTION DISABLED ===")
                    result = {
                        'summary': summary,
                        'reflection': None,
                        'improved': None,
                        'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n*ℹ️ Информация:* Рефлексия отключена в настройках",
                        'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n*ℹ️ Информация:* Рефлексия отключена в настройках"
                    }
                    
                    # Логируем результаты
                    if llm_logger:
                        llm_logger.log_raw_result(summary)
                        llm_logger.log_formatted_result(result['display_text'])
                        llm_logger.log_session_summary(result)
                    
                    return result
                
        except Exception as e:
            logger.error(f"❌ Ошибка анализа с конкретной моделью: {e}")
            return None
    
    async def perform_reflection(self, provider, summary: str, messages: List[Dict], chat_context: Dict, llm_logger=None) -> Optional[str]:
        """
        Выполняет рефлексию над суммаризацией для её улучшения
        
        Args:
            provider: AI провайдер
            summary: Исходная суммаризация
            messages: Сообщения чата
            chat_context: Контекст чата
            
        Returns:
            Результат рефлексии или None при ошибке
        """
        try:
            logger.info("🤔 Начинаем рефлексию над суммаризацией")
            logger.debug(f"Summary length: {len(summary)}")
            logger.debug(f"Messages count: {len(messages)}")
            
            # Создаем промпт для рефлексии
            reflection_prompt = self._create_reflection_prompt(summary, messages, chat_context)
            logger.debug(f"Reflection prompt length: {len(reflection_prompt)}")
            logger.debug(f"=== REFLECTION PROMPT ===")
            logger.debug(reflection_prompt)
            logger.debug(f"=== END REFLECTION PROMPT ===")
            
            # Выполняем рефлексию
            logger.debug("Calling provider.generate_response for reflection...")
            reflection_result = await provider.generate_response(reflection_prompt)
            
            if reflection_result:
                logger.info("✅ Рефлексия выполнена успешно")
                logger.debug(f"Reflection result length: {len(reflection_result)}")
                return reflection_result
            else:
                logger.warning("⚠️ Не удалось получить результат рефлексии")
                logger.debug("Reflection result is None or empty")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении рефлексии: {e}")
            return None
    
    def _create_reflection_prompt(self, summary: str, messages: List[Dict], chat_context: Dict) -> str:
        """
        Создает промпт для рефлексии над суммаризацией
        
        Args:
            summary: Исходная суммаризация
            messages: Сообщения чата
            chat_context: Контекст чата
            
        Returns:
            Промпт для рефлексии
        """
        total_messages = len(messages)
        date = chat_context.get('date', 'неизвестная дата')
        
        return PromptTemplates.get_reflection_prompt(summary, date, total_messages)
    
    async def improve_summary_with_reflection(self, provider, original_summary: str, reflection: str, messages: List[Dict], chat_context: Dict, llm_logger=None) -> Optional[str]:
        """
        Улучшает суммаризацию на основе рефлексии
        
        Args:
            provider: AI провайдер
            original_summary: Исходная суммаризация
            reflection: Результат рефлексии
            messages: Сообщения чата
            chat_context: Контекст чата
            
        Returns:
            Улучшенная суммаризация или None при ошибке
        """
        try:
            logger.info("✨ Начинаем улучшение суммаризации на основе рефлексии")
            
            # Создаем промпт для улучшения
            improvement_prompt = self._create_improvement_prompt(original_summary, reflection, messages, chat_context)
            
            # Выполняем улучшение
            improved_summary = await provider.generate_response(improvement_prompt)
            
            if improved_summary:
                logger.info("✅ Суммаризация успешно улучшена")
                return improved_summary
            else:
                logger.warning("⚠️ Не удалось получить улучшенную суммаризацию")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка при улучшении суммаризации: {e}")
            return None
    
    def _create_improvement_prompt(self, original_summary: str, reflection: str, messages: List[Dict], chat_context: Dict) -> str:
        """
        Создает промпт для улучшения суммаризации на основе рефлексии
        
        Args:
            original_summary: Исходная суммаризация
            reflection: Результат рефлексии
            messages: Сообщения чата
            chat_context: Контекст чата
            
        Returns:
            Промпт для улучшения
        """
        return PromptTemplates.get_improvement_prompt(original_summary, reflection)