# llm_generator_final_FIXED.py - Исправленный импорт

import requests
import json
import chromadb
import logging
from datetime import datetime
from chromadb.utils import embedding_functions
from config import OLLAMA_API_URL, OLLAMA_MODEL, CHROMA_DB_DIR

logger = logging.getLogger(__name__)


def load_prompt_template():
    """Загружает prompt_template.json напрямую"""
    try:
        with open('data/prompt_template.json', 'r', encoding='utf-8') as f:
            template = json.load(f)
            return template
    except FileNotFoundError:
        logger.error("❌ data/prompt_template.json не найден!")
        return None


class DialogueHistory:
    """Управляет историей диалога"""
    
    def __init__(self, max_history=5):
        self.max_history = max_history
        self.history_file = 'data/dialogue_history.json'
        self.history = self.load_history()
    
    def load_history(self):
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def add_message(self, role, text, chat_id=None):
        msg = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "chat_id": chat_id
        }
        self.history.append(msg)
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2:]
        self.save_history()
    
    def clear_chat_history(self, chat_id):
        self.history = [msg for msg in self.history if msg.get('chat_id') != chat_id]
        self.save_history()


class LLMGenerator:
    """Генерирует ответы - ФИНАЛЬНАЯ ВЕРСИЯ"""
    
    def __init__(self):
        self.collection = None
        
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
            self.collection = self.client.get_collection(
                name="user_messages",
                embedding_function=self.embedding_function
            )
            logger.info(f"✅ ChromaDB загружен")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB ошибка: {e}")
        
        self.history = DialogueHistory(max_history=5)
        self.prompt_template = load_prompt_template()
        
        if not self.prompt_template:
            logger.error("❌ Prompt template не загружен!")
            raise RuntimeError("Запусти prompt_generator_advanced.py")
        
        # ТОЛЬКО откровенные утечки промта
        self.bad_patterns = [
            'я не человек',
            'я помощник claude',
            'я помощник от anthropic',
            'я ассистент от openai',
            'я язык модель',
            'следуй этим инструкциям',
            '[инструкция',
            '[система',
            '[промт',
        ]
        
        # Маркеры примеров и инструкций
        self.example_markers = [
            'например:', 'например -', 'примеры:',
            '* прямой,', '* отвечаю', '* не нарушил',
            '- "привет!', '- "как дела',
            'отвечаю коротко', 'критических правил',
        ]
    
    def clean_answer(self, answer):
        """ФИНАЛЬНАЯ фильтрация"""
        if not answer:
            return ""
        
        answer = answer.strip()
        answer_lower = answer.lower()
        
        # УТЕЧКИ ПРОМТА
        for bad in self.bad_patterns:
            if bad in answer_lower:
                logger.warning(f"⚠️ Утечка промта: {bad}")
                return ""
        
        # ПРИМЕРЫ ИЗ ПРОМТА - берем только ДО примеров
        for marker in self.example_markers:
            if marker in answer_lower:
                # Берем текст ДО маркера
                parts = answer_lower.split(marker)
                answer = answer[:len(answer_lower) - len(parts[-1])].strip()
                logger.info(f"🔪 Обрезал примеры после: '{marker}'")
                break
        
        # Удаляем структурные маркеры
        bad_markers = ['ИСТОРИЯ:', '[Вопрос:]', '[Ответ]:', 'Инструкции:']
        for marker in bad_markers:
            if marker in answer:
                answer = answer.split(marker)[0].strip()
        
        # Удаляем маркеры-звездочки (*) в начале строк
        lines = answer.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('* ') or line.startswith('- '):
                # Это пример - пропускаем
                continue
            if line:
                cleaned_lines.append(line)
        
        answer = '\n'.join(cleaned_lines).strip()
        
        # Берем первый абзац если много текста
        paragraphs = answer.split('\n\n')
        if len(paragraphs) > 2 and len(answer) > 600:
            answer = paragraphs[0].strip()
        
        answer = answer.strip()
        
        # ВАЛИДАЦИЯ
        if len(answer) < 3:
            logger.warning(f"⚠️ Слишком короткий ({len(answer)} символов)")
            return ""
        
        if len(answer) > 1000:
            # Обрезаем на точке
            answer = answer[:1000]
            last_period = answer.rfind('.')
            if last_period > 500:
                answer = answer[:last_period + 1]
        
        logger.info(f"✅ Ответ чистый ({len(answer)} символов)")
        return answer
    
    def generate_answer(self, question, chat_id=None):
        """Генерирует ответ"""
        
        logger.info(f"\n🚀 generate_answer: {question[:50]}")
        logger.info(f"📝 URL: {OLLAMA_API_URL}/api/chat")
        logger.info(f"📝 Model: {OLLAMA_MODEL}")
        
        # Получаем system prompt из загруженного template
        system_prompt = self.prompt_template.get('system_prompt', '')
        if not system_prompt:
            logger.error("❌ system_prompt не найден в template!")
            return None
        
        data = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            "stream": False,
            "temperature": 0.7,
            "top_p": 0.85
        }
        
        try:
            resp = requests.post(
                f"{OLLAMA_API_URL}/api/chat",
                json=data,
                timeout=30
            )
            
            logger.info(f"📊 Status: {resp.status_code}")
            
            if resp.status_code == 200:
                result = resp.json()
                answer = result.get('message', {}).get('content', '').strip()
                
                logger.info(f"📥 Сырой ответ: {len(answer)} символов")
                
                answer = self.clean_answer(answer)
                
                if answer:
                    logger.info(f"✨ Финал: {len(answer)} символов")
                    return answer
                else:
                    logger.warning(f"❌ Отфильтрован")
                    return None
            else:
                logger.error(f"❌ Ошибка {resp.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"❌ {e}")
            return None
    
    def generate_final_answer(self, question, chat_id=None):
        """Главная функция"""
        
        for attempt in range(2):
            logger.info(f"\n{'='*60}")
            logger.info(f"⏱️  Попытка {attempt + 1}/2")
            logger.info(f"{'='*60}")
            
            answer = self.generate_answer(question, chat_id)
            
            if answer:
                if chat_id:
                    self.history.add_message("user", question, chat_id)
                    self.history.add_message("assistant", answer, chat_id)
                
                return answer
            
            logger.warning(f"⚠️ Попытка {attempt + 1}/2 не сработала")
        
        logger.error(f"❌ Не удалось после 2 попыток")
        return ""


# Инициализируем
generator = LLMGenerator()


def get_answer(question, chat_id=None, use_history=True):
    return generator.generate_final_answer(question, chat_id)


def clear_history(chat_id):
    generator.history.clear_chat_history(chat_id)
