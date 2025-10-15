import asyncio
import json
import os
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.utils import get_display_name
from dotenv import load_dotenv

load_dotenv()

class TelegramDataCollector:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.client = None
        
    async def init_client(self):
        """Инициализация клиента Telethon"""
        session_name = f"user_{self.user_id}"
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        print(f"✅ Клиент Telegram авторизован для пользователя {self.user_id}")
    
    async def get_dialog_type(self, dialog):
        """Определяем тип диалога"""
        try:
            entity = dialog.entity
            if isinstance(entity, PeerUser):
                return "personal"
            elif isinstance(entity, PeerChat):
                return "group" 
            elif isinstance(entity, PeerChannel):
                if hasattr(entity, 'megagroup') and entity.megagroup:
                    return "group"
                return "channel"
            else:
                return "unknown"
        except:
            return "unknown"
    
    async def collect_user_messages(self, limit_per_chat=100):
        """Сбор сообщений из ВСЕХ типов диалогов"""
        print(f"📥 Собираем сообщения пользователя {self.user_id}...")
        
        me = await self.client.get_me()
        my_id = me.id
        print(f"👤 ID вашего аккаунта: {my_id}")
        
        dialogs = await self.client.get_dialogs(limit=50)
        user_messages = []
        
        print(f"🔍 Найдено диалогов: {len(dialogs)}")
        
        for i, dialog in enumerate(dialogs):
            dialog_name = get_display_name(dialog.entity)
            dialog_type = await self.get_dialog_type(dialog)
            
            print(f"\n--- Диалог {i+1}: {dialog_name} ({dialog_type}) ---")
            
            try:
                message_count = 0
                async for message in self.client.iter_messages(dialog.id, limit=limit_per_chat):
                    if (message.text and 
                        len(message.text.strip()) > 2 and
                        hasattr(message, 'sender_id') and 
                        message.sender_id == my_id):
                        
                        user_messages.append({
                            'text': message.text,
                            'date': message.date.isoformat(),
                            'dialog_with': dialog_name,
                            'dialog_type': dialog_type,
                            'message_id': message.id
                        })
                        message_count += 1
                
                print(f"✅ Собрано сообщений: {message_count}")
                
            except Exception as e:
                print(f"⚠️ Ошибка в диалоге {dialog_name}: {e}")
                continue
        
        return user_messages
    
    async def save_training_data(self, messages):
        """Сохранение данных для обучения"""
        user_dir = f"user_data/{self.user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        filename = f"{user_dir}/training_data.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в {filename}")
        return filename
    
    async def collect_and_save(self):
        """Полный процесс сбора данных"""
        await self.init_client()
        messages = await self.collect_user_messages()
        data_file = await self.save_training_data(messages)
        await self.client.disconnect()
        
        return {
            'user_id': self.user_id,
            'message_count': len(messages),
            'data_file': data_file
        }