# 0_build_vector_db.py - ИНДЕКСИРОВАНИЕ СООБЩЕНИЙ

import json
import logging
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from config import MESSAGES_FILE, CHROMA_DB_DIR, DEBUG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_vector_db():
    """Создает и индексирует ChromaDB базу"""
    
    logger.info("🔍 Анализирую messages...")
    
    # Проверяем что файл с сообщениями существует
    if not Path(MESSAGES_FILE).exists():
        logger.error(f"❌ {MESSAGES_FILE} не найден!")
        logger.info("💡 Совет: Убедись что ты скопировал user_messages.json в data/")
        return False
    
    try:
        # Загружаем сообщения
        with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        if isinstance(messages, dict):
            messages = [msg for msgs in messages.values() for msg in msgs]
        
        if not messages:
            logger.warning("⚠️ Сообщений не найдено в файле")
            return False
        
        logger.info(f"📝 Найдено {len(messages)} сообщений")
        
        # Создаем ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        
        # Удаляем старую collection если существует
        try:
            client.delete_collection(name="user_messages")
        except:
            pass
        
        # Создаем новую
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        collection = client.create_collection(
            name="user_messages",
            embedding_function=embedding_function
        )
        
        logger.info(f"📊 Индексирую {len(messages)} документов...")
        
        # Добавляем сообщения в collection
        ids = [f"msg_{i}" for i in range(len(messages))]
        texts = [str(msg) if isinstance(msg, str) else json.dumps(msg) for msg in messages]
        
        collection.add(ids=ids, documents=texts)
        
        logger.info(f"✅ ChromaDB collection создана!")
        logger.info(f"   Путь: {CHROMA_DB_DIR}")
        logger.info(f"   Документов: {len(messages)}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка при индексировании: {e}")
        return False


if __name__ == "__main__":
    success = build_vector_db()
    exit(0 if success else 1)
