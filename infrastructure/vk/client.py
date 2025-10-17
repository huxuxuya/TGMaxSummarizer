import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime

from python_max_client import MaxClient
from python_max_client.functions.chats import get_chats, get_chat_messages
from python_max_client.functions.users import resolve_users

from .models import VKChat, VKMessage, VKUser
from shared.utils import get_sender_display_name

logger = logging.getLogger(__name__)

class VKMaxClient:
    """Клиент для работы с VK MAX API"""
    
    def __init__(self, token: str):
        self.token = token
        self.client = None
    
    async def connect(self) -> bool:
        """Подключиться к VK MAX"""
        try:
            self.client = MaxClient()
            await self.client.connect()
            await self.client.login_by_token(self.token)
            logger.info("✅ Подключение к VK MAX успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к VK MAX: {e}")
            return False
    
    async def disconnect(self):
        """Отключиться от VK MAX"""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def get_chat_info(self, chat_id: str) -> Optional[VKChat]:
        """Получить информацию о чате"""
        if not self.client:
            return None
        
        try:
            response = get_chats(self.client)
            if "payload" not in response or "chats" not in response["payload"]:
                return None
            
            chats = response["payload"]["chats"]
            for chat in chats:
                if str(chat.get("id")) == str(chat_id):
                    return VKChat(
                        id=str(chat.get("id")),
                        title=chat.get("title", ""),
                        type=chat.get("type", "UNKNOWN"),
                        participants_count=chat.get("participantsCount", 0),
                        description=chat.get("description", "")
                    )
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о чате: {e}")
            return None
    
    async def check_chat_access(self, chat_id: str) -> bool:
        """Проверить доступ к чату"""
        chat_info = await self.get_chat_info(chat_id)
        return chat_info is not None
    
    async def get_available_chats(self) -> List[VKChat]:
        """Получить список всех доступных чатов"""
        if not self.client:
            return []
        
        try:
            response = get_chats(self.client)
            if "payload" not in response or "chats" not in response["payload"]:
                return []
            
            chats = response["payload"]["chats"]
            formatted_chats = []
            
            for chat in chats:
                formatted_chats.append(VKChat(
                    id=str(chat.get("id", "")),
                    title=chat.get("title", "Без названия"),
                    type=chat.get("type", "UNKNOWN"),
                    participants_count=chat.get("participantsCount", 0),
                    description=chat.get("description", "")
                ))
            
            formatted_chats.sort(key=lambda x: x.participants_count, reverse=True)
            
            logger.info(f"✅ Получено {len(formatted_chats)} доступных чатов")
            return formatted_chats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка чатов: {e}")
            return []
    
    async def load_chat_messages(self, chat_id: str, days_back: int = 7, load_only_new: bool = False, last_timestamp: Optional[int] = None) -> List[VKMessage]:
        """Загрузить сообщения чата за последние дни"""
        if not self.client:
            return []
        
        try:
            all_messages = []
            seen_ids = set()
            
            # Определяем начальную точку загрузки
            if load_only_new:
                # Для загрузки новых сообщений начинаем с текущего времени
                last_msg_timestamp = int(datetime.now().timestamp() * 1000)
                logger.info(f"📥 Загружаем только новые сообщения чата {chat_id}...")
            else:
                # Загружаем все сообщения за указанный период
                last_msg_timestamp = int(datetime.now().timestamp() * 1000)
                logger.info(f"📥 Загружаем сообщения чата {chat_id} за последние {days_back} дней...")
            
            batch_count = 0
            user_names = {}
            
            while True:
                try:
                    batch_count += 1
                    
                    response = await get_chat_messages(
                        self.client, 
                        int(chat_id), 
                        count=100, 
                        from_message_id=last_msg_timestamp
                    )
                    
                    if "payload" not in response or "messages" not in response["payload"]:
                        logger.warning("⚠️ Нет данных в ответе")
                        break
                        
                    messages = response["payload"]["messages"]
                    if not messages:
                        logger.info("📭 Больше нет сообщений в чате")
                        break
                        
                    new_messages = []
                    user_ids_to_resolve = set()
                    
                    for msg in messages:
                        msg_id = msg.get('id') or msg.get('messageId')
                        if msg_id and msg_id not in seen_ids:
                            seen_ids.add(msg_id)
                            new_messages.append(msg)
                            
                            sender_id = msg.get('sender')
                            if sender_id and sender_id not in user_names:
                                user_ids_to_resolve.add(sender_id)
                    
                    if not new_messages:
                        break
                        
                    if user_ids_to_resolve:
                        logger.info(f"👤 Получаем имена для {len(user_ids_to_resolve)} пользователей")
                        new_names = await self._get_user_names(list(user_ids_to_resolve))
                        user_names.update(new_names)
                    
                    for msg in new_messages:
                        sender_id = msg.get('sender')
                        default_name = user_names.get(sender_id) if sender_id else None
                        msg['sender_name'] = get_sender_display_name(sender_id, default_name)
                        
                    all_messages.extend(new_messages)
                    logger.info(f"📥 Пакет {batch_count}: загружено {len(new_messages)} новых сообщений")
                    
                    # Проверяем, достигли ли мы последнего сохраненного сообщения (для загрузки новых)
                    if load_only_new and last_timestamp:
                        found_old_message = False
                        for msg in new_messages:
                            if msg.get("time", 0) <= last_timestamp:
                                found_old_message = True
                                break
                        
                        if found_old_message:
                            logger.info("📭 Достигнуто последнее сохраненное сообщение")
                            break
                    
                    last_message = messages[0]
                    last_msg_timestamp = last_message.get("time", 0)
                    
                    if not last_msg_timestamp:
                        logger.error("Не удалось получить timestamp последнего сообщения")
                        break
                        
                    last_msg_timestamp = last_msg_timestamp - 1
                    
                    if len(messages) < 100:
                        logger.info("📭 Достигнут конец чата")
                        break
                        
                    if len(all_messages) > 10000:
                        logger.warning("⚠️ Достигнут лимит в 10000 сообщений")
                        break
                        
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки сообщений: {e}")
                    break
            
            logger.info(f"✅ Загружено {len(all_messages)} сообщений")
            return [VKMessage(**msg) for msg in all_messages]
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки сообщений чата: {e}")
            return []
    
    async def _get_user_names(self, user_ids: List[int]) -> Dict[int, str]:
        """Получить имена пользователей по их ID"""
        if not user_ids:
            return {}
        
        try:
            response = await resolve_users(self.client, list(user_ids))
            if "payload" not in response or "contacts" not in response["payload"]:
                logger.warning(f"⚠️ Нет данных в ответе resolve_users для {user_ids}")
                return {}
                
            names = {}
            contacts = response["payload"]["contacts"]
            logger.info(f"👤 Получено контактов: {len(contacts)}")
            
            for contact in contacts:
                user_id = contact.get("id")
                if user_id:
                    contact_names = contact.get("names", [])
                    if contact_names:
                        name = contact_names[0].get("name", f"User {user_id}")
                    else:
                        name = f"User {user_id}"
                    names[user_id] = name
                    logger.info(f"👤 {user_id} -> {name}")
            return names
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения имен пользователей: {e}")
            return {}
    
    async def format_messages_for_db(self, messages: List[VKMessage], chat_id: str) -> List[Dict]:
        """Форматировать сообщения для сохранения в БД с обработкой изображений"""
        from shared.image_utils import ImageDownloader
        
        image_downloader = ImageDownloader()
        formatted_messages = []
        
        for msg in messages:
            message_id = msg.id or msg.message_id or ""
            sender_id = msg.sender
            text = msg.text or ""
            message_time = msg.time or 0
            
            if message_time:
                dt = datetime.fromtimestamp(message_time / 1000)
                date_str = dt.strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            sender_name = get_sender_display_name(sender_id, None)
            
            # Обрабатываем изображения
            image_paths = []
            if msg.attachments:
                image_paths = await image_downloader.process_message_images(
                    msg.attachments, 
                    chat_id, 
                    message_id
                )
            
            formatted_msg = {
                "message_id": message_id,
                "vk_chat_id": chat_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "text": text,
                "message_time": message_time,
                "date": date_str,
                "message_type": "USER",
                "attachments": msg.attachments,
                "reaction_info": msg.reactions,
                "elements": msg.elements,
                "image_paths": image_paths
            }
            
            formatted_messages.append(formatted_msg)
        
        return formatted_messages

