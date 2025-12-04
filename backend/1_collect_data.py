import json
import os
from telethon.sync import TelegramClient
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, DATA_DIR, MESSAGES_FILE

def collect_all_messages():
    """Собирает ВСЕ исходящие сообщения пользователя из всех диалогов"""
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    client = TelegramClient('session', TELEGRAM_API_ID, TELEGRAM_API_HASH)
    client.start(phone=TELEGRAM_PHONE)
    
    print("[СБОР] Подключено к Telegram")
    
    all_messages = []
    
    # Проходим по всем диалогам
    for dialog in client.iter_dialogs():
        print(f"[СБОР] Обработка диалога: {dialog.title}")
        
        # Собираем ВСЕ исходящие сообщения (без лимита!)
        for message in client.iter_messages(dialog, from_user='me'):
            if message.text:
                all_messages.append({
                    'text': message.text,
                    'date': message.date.isoformat(),
                    'chat_title': dialog.title,
                    'message_id': message.id
                })
    
    # Сохраняем
    with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_messages, f, ensure_ascii=False, indent=2)
    
    print(f"[СБОР] ✅ Собрано {len(all_messages)} сообщений")
    print(f"[СБОР] Сохранено в {MESSAGES_FILE}")
    
    client.disconnect()

if __name__ == "__main__":
    collect_all_messages()
