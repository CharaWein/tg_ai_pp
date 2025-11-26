# 3_telegram_bot_final.py - ОСНОВНОЙ БОТ

import logging
import sys
import time
import requests
from config import BOT_TOKEN, DEBUG
from llm_generator_final import get_answer, clear_history

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def get_updates(offset=None, timeout=30):
    """Получает обновления"""
    try:
        params = {"timeout": timeout, "offset": offset}
        resp = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params, timeout=60)
        return resp.json().get("result", [])
    except Exception as e:
        logger.error(f"❌ Ошибка получения обновлений: {e}")
        return []


def send_message(chat_id, text):
    """Отправляет сообщение"""
    if len(text) > 4096:
        text = text[:4090] + "..."
    
    try:
        params = {"chat_id": chat_id, "text": text}
        requests.post(f"{TELEGRAM_API_URL}/sendMessage", data=params, timeout=10)
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")


def main():
    """Основной цикл бота"""
    
    logger.info("\n" + "="*60)
    logger.info("🟢 RAG AI-клон v4 (FIXED)")
    logger.info("="*60)
    logger.info("📱 Бот готов к работе...")
    logger.info("⌨️  Нажми CTRL+C чтобы остановить\n")
    
    last_update_id = None
    
    while True:
        try:
            updates = get_updates(last_update_id)
            
            for update in updates:
                last_update_id = update.get("update_id", 0) + 1
                
                msg = update.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                username = msg.get("from", {}).get("username", "Unknown")
                text = msg.get("text", "").strip()
                
                if not chat_id or not text:
                    continue
                
                logger.info(f"Q [{chat_id}] (@{username}): {text}")
                
                # Специальные команды
                if text == "/start":
                    send_message(chat_id, "👋 Привет! Я RAG AI-клон. Напиши что-нибудь!")
                    continue
                
                if text == "/clear":
                    clear_history(chat_id)
                    send_message(chat_id, "🗑️ История диалога очищена")
                    continue
                
                # Получаем ответ
                answer = get_answer(text, chat_id=chat_id)
                
                if answer:
                    logger.info(f"A: {answer}\n")
                    send_message(chat_id, answer)
                else:
                    logger.warning(f"A: (empty)\n")
                    send_message(chat_id, "Хм, не знаю что ответить...")
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.info("\n⛔ Бот остановлен")
            break
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
