# config.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ (скопируй прямо сейчас!)

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ========== TELEGRAM ==========
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ========== OLLAMA - ИСПРАВЛЕНО! ==========
# ⚠️ ВАЖНО: БЕЗ /api/generate в конце!
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral:7b"  # ← ИСПРАВЛЕНО! (было gemma3:4b)

# ========== DATA PATHS ==========
DATA_DIR = "data"
MESSAGES_FILE = os.path.join(DATA_DIR, "user_messages.json")
FACTS_FILE = os.path.join(DATA_DIR, "facts_advanced.json")
PROMPT_TEMPLATE_FILE = os.path.join(DATA_DIR, "prompt_template.json")
DIALOGUE_HISTORY_FILE = os.path.join(DATA_DIR, "dialogue_history.json")
CHROMA_DB_DIR = os.path.join(DATA_DIR, "chroma_db")

# ========== DEBUG ==========
DEBUG = True

# ========== ВАЛИДАЦИЯ ==========
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в .env")

if not TELEGRAM_API_ID:
    raise ValueError("❌ TELEGRAM_API_ID не установлен в .env")

# ========== СОЗДАНИЕ ДИРЕКТОРИЙ ==========
Path(DATA_DIR).mkdir(exist_ok=True)
Path(CHROMA_DB_DIR).mkdir(exist_ok=True)

print("✅ Config загружен")
print(f"   OLLAMA_API_URL: {OLLAMA_API_URL}")
print(f"   OLLAMA_MODEL: {OLLAMA_MODEL}")
