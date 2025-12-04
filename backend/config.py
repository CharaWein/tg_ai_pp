# config.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ

import os
from dotenv import load_dotenv
from pathlib import Path
import os

# Автоматическое определение URL для Docker
if os.environ.get('IN_DOCKER') or os.path.exists('/.dockerenv'):
    OLLAMA_API_URL = "http://host.docker.internal:11434"
    print("🐳 Docker: использую host.docker.internal:11434")
else:
    OLLAMA_API_URL = "http://localhost:11434"
    print("🖥️  Хост: использую localhost:11434")


# Загрузка .env первым делом!
load_dotenv()

# ========== БАЗОВЫЕ ПУТИ ==========
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# ========== TELEGRAM ==========
TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PHONE = os.getenv("TELEGRAM_PHONE", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ========== OLLAMA ==========
# OLLAMA_API_URL уже установлен выше в зависимости от окружения
OLLAMA_MODEL = "mistral:7b"

# ========== ФАЙЛЫ ДАННЫХ ==========
MESSAGES_FILE = DATA_DIR / "user_messages.json"
FACTS_FILE = DATA_DIR / "facts_advanced.json"
PROMPT_TEMPLATE_FILE = DATA_DIR / "prompt_template.json"
DIALOGUE_HISTORY_FILE = DATA_DIR / "dialogue_history.json"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# ========== НАСТРОЙКИ ИНДЕКСАЦИИ ==========
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 500
MIN_MESSAGE_LENGTH = 3
MAX_MESSAGE_LENGTH = 5000

# ========== НАСТРОЙКИ ЛОГИРОВАНИЯ ==========
DEBUG = True
LOG_LEVEL = "INFO"

# ========== ВАЛИДАЦИЯ ==========
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в .env")

if not TELEGRAM_API_ID:
    raise ValueError("❌ TELEGRAM_API_ID не установлен в .env")

# ========== СОЗДАНИЕ ДИРЕКТОРИЙ ==========
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

print("✅ Config загружен успешно!")
print(f"   DATA_DIR: {DATA_DIR}")
print(f"   OLLAMA_API_URL: {OLLAMA_API_URL}")
print(f"   OLLAMA_MODEL: {OLLAMA_MODEL}")