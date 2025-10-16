"""
Анализ чатов с помощью модульной системы AI провайдеров
"""
import json
import logging
import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

from ai_providers import ProviderFactory
from config import AI_PROVIDERS, DEFAULT_AI_PROVIDER, FALLBACK_PROVIDERS, ENABLE_REFLECTION, AUTO_IMPROVE_SUMMARY, ENABLE_LLM_LOGGING, LLM_LOGS_DIR
from telegram_formatter import TelegramFormatter
from llm_logger import LLMLogger
from prompts import PromptTemplates
from utils import get_sender_display_name

logger = logging.getLogger(__name__)

def escape_markdown(text: str) -> str:
    """
    DEPRECATED: Эта функция больше не используется.
    Экранирование теперь выполняется через telegramify-markdown в TelegramMessageSender.
    
    Args:
        text: Текст для экранирования
        
    Returns:
        Исходный текст без изменений
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("escape_markdown() is deprecated. Use telegramify-markdown instead.")
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
                elif provider_name == 'ollama':
                    # Для Ollama передаем всю конфигурацию
                    self.config['ollama'] = provider_config
                    logger.debug(f"🔗 DEBUG ChatAnalyzer: ollama config = {provider_config}")
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
                # Создаем провайдера с правильной конфигурацией
                if provider_name == 'ollama' and 'ollama' in self.config:
                    provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
                else:
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
                
                # Создаем провайдера с правильной конфигурацией
                if best_provider_name == 'ollama' and 'ollama' in self.config:
                    provider = self.provider_factory.create_provider(best_provider_name, self.config['ollama'])
                else:
                    provider = self.provider_factory.create_provider(best_provider_name, self.config)
                provider_name = best_provider_name
            
            # Инициализируем провайдера
            if not await provider.initialize():
                logger.error(f"❌ Не удалось инициализировать провайдер: {provider_name}")
                
                # Пробуем fallback провайдеров (кроме Ollama)
                if provider_name != 'ollama':
                    for fallback_name in FALLBACK_PROVIDERS:
                        if fallback_name != provider_name and fallback_name != 'ollama':
                            logger.info(f"🔄 Пробуем fallback провайдер: {fallback_name}")
                            # Создаем fallback провайдера с правильной конфигурацией
                            if fallback_name == 'ollama' and 'ollama' in self.config:
                                fallback_provider = self.provider_factory.create_provider(fallback_name, self.config['ollama'])
                            else:
                                fallback_provider = self.provider_factory.create_provider(fallback_name, self.config)
                            if fallback_provider and await fallback_provider.initialize():
                                provider = fallback_provider
                                provider_name = fallback_name
                                break
                    else:
                        logger.error("❌ Все провайдеры недоступны")
                        return None
                else:
                    logger.error("❌ Ollama недоступен, fallback провайдеры не используются")
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
                # Создаем провайдера с правильной конфигурацией
                if provider_name == 'ollama' and 'ollama' in self.config:
                    provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
                else:
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
                # Создаем провайдера с правильной конфигурацией
                if provider_name == 'ollama' and 'ollama' in self.config:
                    provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
                else:
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
            # Создаем провайдера с правильной конфигурацией
            if provider_name == 'ollama' and 'ollama' in self.config:
                provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
            else:
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
                    
                # Убираем лишние символы
                text = re.sub(r'\s+', ' ', text)
                
                sender_id = msg.get('sender_id')
                sender_name = get_sender_display_name(
                    sender_id,
                    msg.get('sender_name', 'Неизвестно')
                )
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
    
    async def analyze_chat_with_specific_model(self, messages: List[Dict], provider_name: str, model_id: str = None, user_id: int = None, enable_reflection: bool = None, clean_data_first: bool = False) -> Optional[str]:
        """
        Анализ чата с конкретной моделью (для выбора модели при анализе)
        
        Args:
            messages: Список сообщений для анализа
            provider_name: Название провайдера
            model_id: ID модели (для OpenRouter)
            user_id: ID пользователя
            enable_reflection: Переопределение настройки рефлексии (None = использовать глобальную)
            clean_data_first: Предварительная очистка данных через LLM
            
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
                
                # Определяем сценарий
                if clean_data_first:
                    scenario = "with_cleaning"
                elif enable_reflection if enable_reflection is not None else ENABLE_REFLECTION:
                    scenario = "with_reflection"
                else:
                    scenario = "without_reflection"
                
                # Проверяем, есть ли в окружении флаг тестового режима
                test_mode = os.environ.get('TEST_MODE') == 'true'
                
                # Use actual model_id parameter, not environment variable
                llm_logger = LLMLogger(
                    LLM_LOGS_DIR, 
                    date=date, 
                    scenario=scenario,
                    test_mode=test_mode,
                    model_name=model_id  # Use method parameter, not env var
                )
                # НЕ очищаем старые логи - каждый запуск в свою папку
                llm_logger.set_session_info(provider_name, model_id, None, user_id)
                logger.info(f"📁 LLM Logger создан: {llm_logger.get_logs_path()}")
            
            # Создаем провайдера с правильной конфигурацией
            if provider_name == 'ollama' and 'ollama' in self.config:
                provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
            else:
                provider = self.provider_factory.create_provider(provider_name, self.config)
            if not provider:
                logger.error(f"❌ Не удалось создать провайдер: {provider_name}")
                return None
            
            # Устанавливаем логгер в провайдер
            if llm_logger:
                provider.set_llm_logger(llm_logger)
            
            # Если указана модель, устанавливаем её ДО инициализации провайдера
            if model_id and hasattr(provider, 'set_model'):
                provider.set_model(model_id)
                logger.info(f"🔗 Установлена модель {provider_name}: {model_id}")
            
            # Инициализируем провайдера
            if not await provider.initialize():
                logger.error(f"❌ Не удалось инициализировать провайдер: {provider_name}")
                return None
            
            # Оптимизация и логирование теперь происходит в провайдерах
            
            # Логируем входные сообщения (сырые данные)
            if llm_logger:
                llm_logger.log_input_messages_raw(messages)
            
            # Предварительная очистка данных, если требуется (САМЫЙ ПЕРВЫЙ ШАГ)
            if clean_data_first:
                logger.info("🧹 Выполняем предварительную очистку данных...")
                
                # Создаем временный контекст для очистки
                temp_chat_context = {
                    'total_messages': len(messages),
                    'date': messages[0].get('message_time', 0) if messages else 0,
                    'provider': provider_name,
                    'model': model_id
                }
                
                messages = await self.clean_messages(provider, messages, temp_chat_context, llm_logger)
                if not messages:
                    logger.error("❌ Очистка данных не удалась или не осталось сообщений")
                    return None
                logger.info(f"✅ Очистка завершена, осталось {len(messages)} сообщений")
                
                # Логируем отфильтрованные сообщения
                if llm_logger:
                    llm_logger.log_filtered_messages_raw(messages)
            
            # Создаем контекст чата (после очистки, если она была)
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
                logger.debug(f"enable_reflection override: {enable_reflection}")
                
                # Определяем, нужно ли выполнять рефлексию
                should_reflect = enable_reflection if enable_reflection is not None else ENABLE_REFLECTION
                logger.debug(f"should_reflect: {should_reflect}")
                
                if should_reflect:
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
                            llm_logger.log_final_result_raw(result)
                        
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
                                    'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n🤔 *Рефлексия и анализ*\n{escaped_reflection}\n\n✨ *Улучшенная суммаризация*\n{escaped_improved}",
                                    'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n||🤔 Рефлексия и анализ:||\n||{escaped_reflection}||\n\n||✨ Улучшенная суммаризация:||\n||{escaped_improved}||"
                                }
                                
                                # Логируем результаты
                                if llm_logger:
                                    llm_logger.log_raw_result(summary)
                                    llm_logger.log_formatted_result(result['display_text'])
                                    llm_logger.log_session_summary(result)
                                    llm_logger.log_final_result_raw(result)
                                
                                return result
                            else:
                                logger.warning("⚠️ Не удалось улучшить суммаризацию, показываем с рефлексией")
                                result = {
                                    'summary': summary,
                                    'reflection': reflection,
                                    'improved': None,
                                    'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n🤔 *Рефлексия и улучшения*\n{escaped_reflection}",
                                    'display_text_alt': f"*📝 Исходная суммаризация:*\n{summary}\n\n||🤔 Рефлексия и улучшения:||\n||{escaped_reflection}||"
                                }
                                
                                # Логируем результаты
                                if llm_logger:
                                    llm_logger.log_raw_result(summary)
                                    llm_logger.log_formatted_result(result['display_text'])
                                    llm_logger.log_session_summary(result)
                                    llm_logger.log_final_result_raw(result)
                                
                                return result
                        else:
                            result = {
                                'summary': summary,
                                'reflection': reflection,
                                'improved': None,
                                'display_text': f"*📝 Исходная суммаризация:*\n{summary}\n\n🤔 *Рефлексия и улучшения*\n{escaped_reflection}",
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
                        llm_logger.log_final_result_raw(result)
                    
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
            
            # Логируем запрос на улучшение
            if llm_logger:
                llm_logger.log_improvement_request(improvement_prompt)
            
            # Выполняем улучшение
            import time
            start_time = time.time()
            improved_summary = await provider.generate_response(improvement_prompt)
            end_time = time.time()
            response_time = end_time - start_time
            
            # Логируем ответ на улучшение
            if llm_logger and improved_summary:
                llm_logger.log_improvement_response(improved_summary, response_time)
                llm_logger.log_stage_time('improvement', response_time)
            
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
    
    async def clean_messages(self, provider, messages: List[Dict], chat_context: dict, llm_logger = None) -> List[Dict]:
        """
        Очистка сообщений через LLM перед суммаризацией
        Удаляет шум, координацию, микроменеджмент
        
        Args:
            provider: Провайдер AI
            messages: Список сообщений для очистки
            chat_context: Контекст чата
            llm_logger: Логгер для записи запросов
            
        Returns:
            Отфильтрованный список сообщений
        """
        try:
            logger.info(f"🧹 Начинаем очистку {len(messages)} сообщений...")
            
            # Подготавливаем данные для промпта
            messages_text = ""
            for i, msg in enumerate(messages):
                message_id = msg.get('id', i)
                text = msg.get('text', '').strip()
                if text:
                    messages_text += f"ID: {message_id}\nТекст: {text}\n\n"
            
            if not messages_text.strip():
                logger.warning("⚠️ Нет текстовых сообщений для очистки")
                return messages
            
            # Создаем промпт для очистки
            from prompts import PromptTemplates
            cleaning_prompt = PromptTemplates.DATA_CLEANING_PROMPT.format(messages=messages_text)
            
            # Логируем запрос очистки
            if llm_logger:
                llm_logger.log_cleaning_request(cleaning_prompt)
            
            # Выполняем очистку через LLM
            import time
            start_time = time.time()
            response = await provider.generate_response(cleaning_prompt)
            end_time = time.time()
            response_time = end_time - start_time
            
            if not response:
                logger.error("❌ Не удалось получить ответ от LLM для очистки данных")
                return messages
            
            # Логируем ответ очистки
            if llm_logger:
                llm_logger.log_cleaning_response(response, response_time)
                llm_logger.log_stage_time('cleaning', response_time)
            
            # Парсим JSON ответ
            import json
            import re
            
            # Извлекаем JSON из ответа (может быть обернут в текст)
            json_match = re.search(r'\[[\d,\s]+\]', response)
            if not json_match:
                logger.error(f"❌ Не удалось найти JSON массив в ответе: {response}")
                return messages
            
            try:
                selected_ids = json.loads(json_match.group())
                logger.info(f"✅ LLM выбрал {len(selected_ids)} сообщений из {len(messages)}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON: {e}")
                return messages
            
            # Фильтруем сообщения по выбранным ID
            cleaned_messages = []
            for i, msg in enumerate(messages):
                message_id = msg.get('id', i)
                if message_id in selected_ids:
                    cleaned_messages.append(msg)
            
            logger.info(f"✅ Очистка завершена: {len(cleaned_messages)} из {len(messages)} сообщений")
            return cleaned_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке сообщений: {e}")
            return messages
    
    async def structured_analysis(self, provider, messages: List[Dict], chat_context: dict, llm_logger=None) -> dict:
        """
        Структурированный анализ с классификацией и экстракцией
        
        Args:
            provider: Провайдер AI
            messages: Список сообщений для анализа
            chat_context: Контекст чата
            llm_logger: Логгер для записи запросов
            
        Returns:
            Словарь с результатами анализа
        """
        try:
            logger.info("🔍 Начинаем структурированный анализ...")
            
            # Шаг 1: Классификация сообщений
            logger.info("📊 Шаг 1: Классификация сообщений...")
            classification = await self._classify_messages(provider, messages, llm_logger)
            
            if not classification:
                logger.error("❌ Классификация не удалась")
                return None
            
            # Фильтруем irrelevant сообщения
            relevant_messages = self._filter_by_classification(messages, classification)
            logger.info(f"✅ Классификация завершена: {len(relevant_messages)} релевантных из {len(messages)} сообщений")
            
            # Шаг 2: Экстракция слотов
            logger.info("🔍 Шаг 2: Экстракция слотов...")
            events = await self._extract_slots(provider, relevant_messages, classification, llm_logger)
            
            if not events:
                logger.error("❌ Экстракция слотов не удалась")
                return None
            
            logger.info(f"✅ Экстракция завершена: {len(events)} событий")
            
            # Шаг 3: Финальная сводка
            logger.info("📝 Шаг 3: Генерация сводки для родителей...")
            summary = await self._generate_parent_summary(provider, events, llm_logger)
            
            if not summary:
                logger.error("❌ Генерация сводки не удалась")
                return None
            
            logger.info("✅ Структурированный анализ завершен успешно")
            
            return {
                'summary': summary,
                'events': events,
                'classification': classification
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при структурированном анализе: {e}")
            return None
    
    async def _classify_messages(self, provider, messages: List[Dict], llm_logger=None, retry_count=0, stream_callback=None) -> List[Dict]:
        """
        Классификация сообщений с повторной попыткой при невалидном JSON
        
        Args:
            provider: Провайдер AI
            messages: Список сообщений
            llm_logger: Логгер
            retry_count: Количество попыток
            
        Returns:
            Список классифицированных сообщений
        """
        try:
            # Импортируем промпт
            from prompts import MESSAGE_CLASSIFICATION_PROMPT
            
            # Формируем JSON для промпта
            messages_json = json.dumps([{"id": msg.get('message_id', msg.get('id', '')), "text": msg.get('text')} for msg in messages], ensure_ascii=False)
            
            # Формируем промпт
            prompt = MESSAGE_CLASSIFICATION_PROMPT.format(messages_json=messages_json)
            
            # Логируем запрос
            if llm_logger:
                llm_logger.log_classification_request(prompt)
            
            # Получаем ответ
            import time
            start_time = time.time()
            response = await provider.generate_response(prompt, stream_callback=stream_callback)
            end_time = time.time()
            response_time = end_time - start_time
            
            if not response:
                logger.error("❌ Не удалось получить ответ от LLM для классификации")
                return []
            
            # Логируем ответ
            if llm_logger:
                llm_logger.log_classification_response(response, response_time)
                llm_logger.log_stage_time('classification', response_time)
            
            # Валидация JSON
            try:
                # Очищаем ответ от markdown блоков
                cleaned_response = self._clean_json_response(response)
                classification = json.loads(cleaned_response)
                logger.info(f"✅ Классификация получена: {len(classification)} сообщений")
                return classification
            except json.JSONDecodeError as e:
                if retry_count < 2:
                    logger.warning(f"⚠️ Ошибка парсинга JSON (попытка {retry_count + 1}): {str(e)}")
                    # Повторная попытка с указанием ошибки
                    error_prompt = f"{prompt}\n\nОШИБКА ПАРСИНГА JSON: {str(e)}\nИсправь формат и верни только валидный JSON-массив."
                    return await self._classify_messages_with_error(provider, error_prompt, llm_logger, retry_count + 1)
                else:
                    logger.error(f"❌ Не удалось получить валидный JSON после {retry_count + 1} попыток")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при классификации сообщений: {e}")
            return []
    
    async def _classify_messages_with_error(self, provider, error_prompt: str, llm_logger=None, retry_count=0) -> List[Dict]:
        """
        Повторная попытка классификации с указанием ошибки
        
        Args:
            provider: Провайдер AI
            error_prompt: Промпт с указанием ошибки
            llm_logger: Логгер
            retry_count: Количество попыток
            
        Returns:
            Список классифицированных сообщений
        """
        try:
            # Получаем ответ
            import time
            start_time = time.time()
            response = await provider.generate_response(error_prompt)
            end_time = time.time()
            response_time = end_time - start_time
            
            if not response:
                logger.error("❌ Не удалось получить ответ от LLM для повторной классификации")
                return []
            
            # Логируем ответ
            if llm_logger:
                llm_logger.log_classification_response(response, response_time)
                llm_logger.log_stage_time('classification', response_time)
            
            # Валидация JSON
            try:
                # Очищаем ответ от markdown блоков
                cleaned_response = self._clean_json_response(response)
                classification = json.loads(cleaned_response)
                logger.info(f"✅ Повторная классификация успешна: {len(classification)} сообщений")
                return classification
            except json.JSONDecodeError as e:
                if retry_count < 2:
                    logger.warning(f"⚠️ Ошибка парсинга JSON при повторной попытке (попытка {retry_count + 1}): {str(e)}")
                    # Еще одна попытка
                    new_error_prompt = f"{error_prompt}\n\nОШИБКА ПАРСИНГА JSON: {str(e)}\nИсправь формат и верни только валидный JSON-массив."
                    return await self._classify_messages_with_error(provider, new_error_prompt, llm_logger, retry_count + 1)
                else:
                    logger.error(f"❌ Не удалось получить валидный JSON после {retry_count + 1} повторных попыток")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при повторной классификации: {e}")
            return []
    
    def _filter_by_classification(self, messages: List[Dict], classification: List[Dict]) -> List[Dict]:
        """
        Фильтрует сообщения по результатам классификации, исключая irrelevant
        
        Args:
            messages: Исходные сообщения
            classification: Результаты классификации
            
        Returns:
            Отфильтрованные сообщения
        """
        try:
            # Создаем словарь классификации для быстрого поиска
            classification_dict = {item.get('message_id', item.get('id')): item.get('class') for item in classification}
            
            # Фильтруем сообщения
            relevant_messages = []
            for msg in messages:
                message_id = str(msg.get('message_id', msg.get('id', '')))
                msg_class = classification_dict.get(message_id)
                
                if msg_class and msg_class != 'irrelevant':
                    relevant_messages.append(msg)
            
            logger.info(f"✅ Фильтрация завершена: {len(relevant_messages)} релевантных из {len(messages)} сообщений")
            return relevant_messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка при фильтрации сообщений: {e}")
            return messages
    
    async def _extract_slots(self, provider, messages: List[Dict], classification: List[Dict], llm_logger=None, stream_callback=None) -> List[Dict]:
        """
        Экстракция слотов из сообщений
        
        Args:
            provider: Провайдер AI
            messages: Список сообщений
            classification: Результаты классификации
            llm_logger: Логгер
            
        Returns:
            Список извлеченных событий
        """
        try:
            # Импортируем промпт
            from prompts import SLOT_EXTRACTION_PROMPT
            
            # Создаем словарь классификации для быстрого поиска
            classification_dict = {item.get('message_id'): item.get('class') for item in classification}
            
            # Формируем JSON для промпта с включением класса
            messages_with_class = []
            for msg in messages:
                message_id = str(msg.get('message_id', msg.get('id', '')))
                msg_class = classification_dict.get(message_id, 'unknown')
                messages_with_class.append({
                    "id": message_id,
                    "text": msg.get('text'),
                    "type": msg_class
                })
            
            messages_json = json.dumps(messages_with_class, ensure_ascii=False)
            
            # Формируем промпт
            prompt = SLOT_EXTRACTION_PROMPT.format(messages_json=messages_json)
            
            # Логируем запрос
            if llm_logger:
                llm_logger.log_extraction_request(prompt)
            
            # Получаем ответ
            import time
            start_time = time.time()
            response = await provider.generate_response(prompt, stream_callback=stream_callback)
            end_time = time.time()
            response_time = end_time - start_time
            
            if not response:
                logger.error("❌ Не удалось получить ответ от LLM для экстракции")
                return []
            
            # Логируем ответ
            if llm_logger:
                llm_logger.log_extraction_response(response, response_time)
                llm_logger.log_stage_time('extraction', response_time)
            
            # Валидация JSON
            try:
                # Очищаем ответ от markdown блоков
                cleaned_response = self._clean_json_response(response)
                events = json.loads(cleaned_response)
                logger.info(f"✅ Экстракция завершена: {len(events)} событий")
                return events
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON при экстракции: {str(e)}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Ошибка при экстракции слотов: {e}")
            return []
    
    async def _generate_parent_summary(self, provider, events: List[Dict], llm_logger=None, stream_callback=None) -> str:
        """
        Генерация итоговой сводки для родителей
        
        Args:
            provider: Провайдер AI
            events: Список извлеченных событий
            llm_logger: Логгер
            
        Returns:
            Текст сводки для родителей
        """
        try:
            # Импортируем промпт
            from prompts import PARENT_SUMMARY_PROMPT
            
            # Формируем JSON для промпта
            events_json = json.dumps(events, ensure_ascii=False, indent=2)
            
            # Формируем промпт
            prompt = PARENT_SUMMARY_PROMPT.format(events_json=events_json)
            
            # Логируем запрос
            if llm_logger:
                llm_logger.log_parent_summary_request(prompt)
            
            # Получаем ответ
            import time
            start_time = time.time()
            response = await provider.generate_response(prompt, stream_callback=stream_callback)
            end_time = time.time()
            response_time = end_time - start_time
            
            if not response:
                logger.error("❌ Не удалось получить ответ от LLM для генерации сводки")
                return None
            
            # Логируем ответ
            if llm_logger:
                llm_logger.log_parent_summary_response(response, response_time)
                llm_logger.log_stage_time('parent_summary', response_time)
            
            logger.info("✅ Сводка для родителей сгенерирована")
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка при генерации сводки для родителей: {e}")
            return None
    
    async def structured_analysis_with_specific_model(self, messages: List[Dict], provider_name: str, model_name: str, user_id: int) -> dict:
        """
        Структурированный анализ с конкретной моделью
        
        Args:
            messages: Список сообщений для анализа
            provider_name: Имя провайдера
            model_name: Имя модели
            user_id: ID пользователя
            
        Returns:
            Результат структурированного анализа
        """
        try:
            # Создаем провайдер с правильной конфигурацией
            if provider_name == 'ollama' and 'ollama' in self.config:
                provider = self.provider_factory.create_provider(provider_name, self.config['ollama'])
            else:
                provider = self.provider_factory.create_provider(provider_name, self.config)
            if not provider:
                logger.error(f"❌ Не удалось создать провайдер {provider_name}")
                return None
            
            # Устанавливаем модель
            if model_name:
                provider.set_model(model_name)
            
            # Создаем контекст чата
            chat_context = {
                'total_messages': len(messages),
                'date': messages[0].get('date') if messages else None,
                'chat_id': messages[0].get('vk_chat_id') if messages else None
            }
            
            # Создаем логгер с учетом TEST_MODE
            chat_id_for_logger = str(chat_context.get('chat_id', 'unknown'))
            
            # Check TEST_MODE
            test_mode = os.environ.get('TEST_MODE') == 'true'
            
            # Always use model_name parameter, not TEST_MODEL_NAME
            llm_logger = LLMLogger(
                scenario="structured_analysis",
                model_name=model_name,  # ✅ Use actual model parameter
                test_mode=test_mode     # ✅ Pass test_mode flag
            )
            
            # Устанавливаем метаданные сессии
            llm_logger.set_session_info(provider_name, model_name, chat_id_for_logger, user_id)
            
            # Выполняем структурированный анализ
            result = await self.structured_analysis(provider, messages, chat_context, llm_logger)
            
            if result:
                # Логируем сырой результат
                if llm_logger:
                    llm_logger.log_raw_result(result.get('summary', ''))
                    llm_logger.log_formatted_result(result.get('summary', ''))
                    llm_logger.log_session_summary({
                        'summary': result.get('summary'),
                        'events': result.get('events'),
                        'classification': result.get('classification')
                    })
                
                # Возвращаем результат в формате, совместимом с существующей системой
                return {
                    'summary': result.get('summary', ''),
                    'display_text': result.get('summary', ''),
                    'events': result.get('events', []),
                    'classification': result.get('classification', [])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка при структурированном анализе с моделью: {e}")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """
        Очищает ответ от markdown блоков и лишнего текста для получения чистого JSON
        
        Args:
            response: Ответ от модели
            
        Returns:
            Очищенный JSON
        """
        try:
            # Убираем markdown блоки ```json ... ```
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            # Убираем лишние пробелы и переносы строк
            response = response.strip()
            
            # Ищем начало и конец JSON массива
            start_bracket = response.find('[')
            end_bracket = response.rfind(']')
            
            if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
                response = response[start_bracket:end_bracket + 1]
            
            return response
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при очистке JSON ответа: {e}")
            return response
    
    async def get_available_ollama_models(self) -> List[str]:
        """
        Получить список доступных моделей с сервера Ollama
        
        Returns:
            List[str]: Список имен доступных моделей
        """
        import aiohttp
        
        try:
            # Получаем URL сервера Ollama из конфигурации
            ollama_base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ollama_base_url}/api/tags", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model_info in data.get('models', []):
                            model_name = model_info.get('name', '')
                            if model_name:
                                models.append(model_name)
                        logger.info(f"✅ Получено {len(models)} моделей Ollama")
                        return models
                    else:
                        logger.error(f"❌ Ошибка получения моделей Ollama: HTTP {response.status}")
                        return []
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка подключения к Ollama: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при получении моделей Ollama: {e}")
            return []