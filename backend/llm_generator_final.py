import requests
import json
import logging
import time
from config import OLLAMA_API_URL, OLLAMA_MODEL, PROMPT_TEMPLATE_FILE

logger = logging.getLogger(__name__)

# НАСТРОЙКИ
TIMEOUT = 300  # 5 минут (увеличено для больших промптов)
MAX_RETRIES = 3  # Количество попыток при ошибках

def load_prompt_template():
    """Загружает prompt_template.json из config"""
    try:
        path = PROMPT_TEMPLATE_FILE
        if not path.exists():
            logger.error(f"❌ {path} не найден!")
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        system_prompt = data.get('system_prompt', '').strip()
        if not system_prompt:
            logger.error("❌ system_prompt пустой!")
            return None
        
        logger.info(f"✅ Загружен промт ({len(system_prompt)} символов)")
        return system_prompt
        
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки промта: {e}")
        return None

def generate_answer_simple(question, chat_id=None):
    """Простая версия генерации ответа"""
    system_prompt = load_prompt_template()
    if not system_prompt:
        return None
    
    # Обрезаем промт если слишком длинный
    if len(system_prompt) > 2000:
        system_prompt = system_prompt[:2000]
        logger.info(f"📝 Обрезан промт до 2000 символов")
    
    logger.info(f"📤 Отправляю запрос к Ollama...")
    logger.info(f"   URL: {OLLAMA_API_URL}/api/chat")
    logger.info(f"   Вопрос: {question[:50]}...")
    
    # Используем /api/chat для лучшей поддержки диалогов
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{OLLAMA_API_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 300,
                        "top_p": 0.85
                    }
                },
                timeout=TIMEOUT
            )
            
            logger.info(f"📥 Получен ответ: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("message", {}).get("content", "").strip()
                
                if not answer:
                    logger.warning("⚠️ Пустой ответ от LLM")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(f"🔄 Повторная попытка через {wait_time} сек...")
                        time.sleep(wait_time)
                        continue
                    return None
                
                logger.info(f"✅ Ответ ({len(answer)} символов): {answer[:100]}...")
                
                # Простая очистка
                answer = clean_answer(answer)
                return answer
                
            elif response.status_code == 500:
                wait_time = (attempt + 1) * 3
                logger.warning(f"⚠️ Ошибка 500 от Ollama (попытка {attempt + 1}/{MAX_RETRIES}). Жду {wait_time} сек...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Ошибка HTTP 500 после всех попыток")
                    return None
            else:
                logger.error(f"❌ Ошибка HTTP {response.status_code}")
                logger.error(f"Текст ответа: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            wait_time = (attempt + 1) * 5
            logger.warning(f"⏱️ Таймаут при вызове Ollama (попытка {attempt + 1}/{MAX_RETRIES}). Жду {wait_time} сек...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Таймаут ({TIMEOUT} секунд) после всех попыток")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Не могу подключиться к Ollama")
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 2
                logger.warning(f"🔄 Повторная попытка через {wait_time} сек...")
                time.sleep(wait_time)
                continue
            return None
    
    return None

def clean_answer(answer):
    """Очистка ответа"""
    if not answer:
        return ""
    
    answer = answer.strip()
    
    # Удаляем маркеры промта
    bad_patterns = [
        "Я не человек",
        "Я помощник",
        "Я язык модель",
        "[система",
        "[инструкция",
    ]
    
    for pattern in bad_patterns:
        if pattern.lower() in answer.lower():
            # Удаляем все после маркера
            idx = answer.lower().find(pattern.lower())
            if idx > 0:
                answer = answer[:idx].strip()
    
    # Удаляем примеры из промта
    example_markers = [
        "например:",
        "например -",
        "примеры:",
        "* ",
        "- ",
    ]
    
    for marker in example_markers:
        if marker in answer:
            parts = answer.split(marker, 1)
            if len(parts[0]) > 10:  # Если есть текст до маркера
                answer = parts[0].strip()
    
    # Обрезаем слишком длинные ответы
    if len(answer) > 1000:
        answer = answer[:1000]
        # Обрезаем на последней точке
        last_dot = answer.rfind('.')
        if last_dot > 500:
            answer = answer[:last_dot + 1]
    
    return answer

def get_answer(question, chat_id=None):
    """Главная функция для бота"""
    logger.info(f"\n{'='*60}")
    logger.info(f"👤 Вопрос: {question}")
    logger.info(f"{'='*60}")
    
    # Попробуем 2 раза
    for attempt in range(2):
        logger.info(f"🔄 Попытка {attempt + 1}/2")
        
        answer = generate_answer_simple(question, chat_id)
        
        if answer and len(answer) > 5:
            logger.info(f"✅ Успех! Ответ: {answer[:80]}...")
            return answer
        
        logger.warning(f"⚠️ Попытка {attempt + 1} не удалась")
    
    logger.error("❌ Не удалось получить ответ после 2 попыток")
    return "Хм, не знаю что ответить..."

def clear_history(chat_id):
    """Заглушка для очистки истории"""
    pass

# Тест
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("🔧 Тест генератора ответов...")
    
    test_question = "Привет! Как дела?"
    answer = get_answer(test_question)
    
    print(f"\n📝 Вопрос: {test_question}")
    print(f"💬 Ответ: {answer}")