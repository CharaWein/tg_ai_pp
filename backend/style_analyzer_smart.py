# style_analyzer_smart_v2.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
# ✅ Убрана фильтрация 'привет', добавлена обработка ошибок, дополнены примеры

import json
import chromadb
import re
from collections import Counter
from chromadb.utils import embedding_functions
from config import CHROMA_DB_DIR

def is_valid_response(msg):
    """Проверяет, валидный ли это ответ"""
    if not msg or len(msg) < 2:
        return False
    
    # Спам маркеры
    spam_markers = ['http', 'ку', 'жж', 'uvk', 'jn', '***']
    if any(marker in msg.lower() for marker in spam_markers):
        return False
    
    # Слишком много пунктуации
    if '!!!!' in msg or '????' in msg:
        return False
    
    return True

def extract_style_features(messages):
    """Анализирует стиль с фильтрацией"""
    valid_messages = [msg for msg in messages if is_valid_response(msg)]
    
    if not valid_messages:
        return {
            "sentence_starts": [],
            "frequent_phrases": [],
            "punctuation": {},
            "avg_sentence_length": 50,
            "sentence_lengths": []
        }
    
    print(f"📊 Валидных сообщений: {len(valid_messages)} из {len(messages)}")
    
    sentence_starts = []
    phrase_patterns = []
    punctuation_marks = Counter()
    sentence_lengths = []
    russian_stopwords = {
        'и', 'в', 'на', 'по', 'но', 'или', 'что', 'как', 'где', 'когда',
        'если', 'то', 'это', 'не', 'да', 'нет', 'а', 'к', 'с', 'за'
    }
    
    for msg in valid_messages:
        msg_clean = msg.strip()
        
        # Начало предложения
        words = msg_clean.split()[:3]
        if words and len(' '.join(words)) > 3:
            start = ' '.join(words).lower()
            sentence_starts.append(start)
        
        # Длина
        sentence_lengths.append(len(msg_clean))
        
        # Пунктуация
        for char in msg_clean:
            if char in '!?.,-;:()':
                punctuation_marks[char] += 1
        
        # Частые последовательности
        words_lower = [w.lower() for w in words if w.lower() not in russian_stopwords and len(w) > 2]
        if len(words_lower) >= 2:
            phrase_patterns.append(' '.join(words_lower[:2]))
    
    top_starts = Counter(sentence_starts).most_common(15)
    filtered_starts = [(s, count) for s, count in top_starts if count >= 2]
    
    return {
        "sentence_starts": filtered_starts if filtered_starts else top_starts[:5],
        "frequent_phrases": Counter(phrase_patterns).most_common(10),
        "punctuation": dict(punctuation_marks.most_common(10)),
        "avg_sentence_length": sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 50,
        "sentence_lengths": sentence_lengths
    }

def extract_tone_markers(messages):
    """Ищет маркеры тона"""
    tone_patterns = {
        "ироничный": {
            "markers": ['щас', 'лол', 'ну да', 'конечно', 'кек', 'хахах'],
            "count": 0
        },
        "прямой": {
            "markers": ['просто', 'в принципе', 'в целом', 'по факту'],
            "count": 0
        },
        "вопрошающий": {
            "markers": ['а почему', 'зачем', 'откуда', 'как так'],
            "count": 0
        },
        "творческий": {
            "markers": ['может', 'интересно', 'представляю', 'звучит'],
            "count": 0
        },
        "серьезный": {
            "markers": ['считаю', 'думаю', 'мнение', 'убежден'],
            "count": 0
        }
    }
    
    msg_combined = ' '.join([m for m in messages if is_valid_response(m)]).lower()
    
    for tone, data in tone_patterns.items():
        for marker in data["markers"]:
            count = msg_combined.count(marker)
            tone_patterns[tone]["count"] += count
    
    sorted_tones = sorted(
        [(tone, data["count"]) for tone, data in tone_patterns.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    # Берем только тоны с хотя бы 1 маркером
    return [(tone, count) for tone, count in sorted_tones if count > 0]

def extract_response_patterns(messages):
    """Анализирует паттерны ответов"""
    valid_messages = [msg for msg in messages if is_valid_response(msg)]
    
    response_patterns = {
        "greeting": [],
        "status": [],
        "identity": [],
        "action": [],
        "opinion": []
    }
    
    for msg in valid_messages:
        msg_lower = msg.lower().strip()
        
        # Приветствия
        if any(x in msg_lower for x in ['привет', 'хай', 'hello', 'салют', 'пока']):
            if 2 < len(msg) < 50:
                response_patterns["greeting"].append(msg.strip())
        
        # Статус
        elif any(x in msg_lower for x in ['норм', 'пойдёт', 'хорошо', 'отлично', 'так себе']):
            if 2 < len(msg) < 100:
                response_patterns["status"].append(msg.strip())
        
        # Личность
        elif any(x in msg_lower for x in ['я ', 'имя', 'зовут', 'зову', 'андрей']):
            if 2 < len(msg) < 100:
                response_patterns["identity"].append(msg.strip())
        
        # Действия
        elif any(x in msg_lower for x in ['делаю', 'занят', 'кодирую', 'смотрю', 'развлекаюсь']):
            if 5 < len(msg) < 200:
                response_patterns["action"].append(msg.strip())
        
        # Мнения
        elif any(x in msg_lower for x in ['думаю', 'считаю', 'мнение', 'кажется']):
            if 5 < len(msg) < 200:
                response_patterns["opinion"].append(msg.strip())
    
    # Очищаем и берем ТОП
    for key in response_patterns:
        unique_patterns = list(set(response_patterns[key]))
        response_patterns[key] = unique_patterns[:5]
    
    return response_patterns

def build_smart_system_prompt(facts, style_features, tone_markers, response_patterns):
    """Создает умный промт"""
    personal = facts.get('personal', {})
    location = facts.get('location', {})
    hobbies = facts.get('hobbies', {})
    beliefs = facts.get('beliefs', {})
    social = facts.get('social', {})
    
    # Безопасные значения по умолчанию
    common_starts = style_features.get('sentence_starts', [])
    starts_str = ', '.join([f'"{start}"' for start, _ in common_starts[:4]]) if common_starts else '"здравствуй"'
    
    punctuation = style_features.get('punctuation', {})
    main_punct = max(punctuation.items(), key=lambda x: x[1])[0] if punctuation else '.'
    
    tones = [tone for tone, _ in tone_markers[:2]]
    tone_desc = ', '.join(tones) if tones else 'прямой'
    
    avg_len = style_features.get('avg_sentence_length', 60)
    
    # Примеры ответов с защитой от пустоты
    greeting_examples = response_patterns.get('greeting', [f'Привет{main_punct}'])
    status_examples = response_patterns.get('status', [f'Норм{main_punct}'])
    action_examples = response_patterns.get('action', ['Кодирую обычно.'])
    
    if not greeting_examples:
        greeting_examples = [f'Привет{main_punct}']
    if not status_examples:
        status_examples = [f'Норм{main_punct}']
    
    system_prompt = f"""Ты — {personal.get('full_name', 'Андрей')}, {personal.get('age', '25')} лет, из {location.get('current_city', 'Москвы')}.

=== ТВОЙ СТИЛЬ (РЕАЛЬНЫЙ) ===

МАНЕРА РЕЧИ:
- Тон: {tone_desc}
- Как начинаешь: {starts_str}
- Пунктуация: {main_punct}
- Средняя длина: ~{round(avg_len)} символов
- Стиль: Естественный, без шаблонов

ФАКТЫ О СЕБЕ:
- Люблю: {', '.join(hobbies.get('likes', ['кодирование'])[:5])}
- Музыка: {hobbies.get('music', 'разная')}
- Программирование: {'да' if hobbies.get('programming') else 'нет'}
- Стратегические игры: {'да' if hobbies.get('strategy_games') else 'нет'}
- Друзья: {', '.join(social.get('friends', [])[:3]) if social.get('friends') else 'есть'}
- Лучший друг: {social.get('best_friend', 'не указан')}

УБЕЖДЕНИЯ:
{'; '.join(beliefs.get('core_beliefs', [])[:2]) if beliefs.get('core_beliefs') else 'Ценю честность и логику'}

=== ПРИМЕРЫ ТВОИХ ОТВЕТОВ ===

На "привет":
{chr(10).join(['  ' + ex for ex in greeting_examples[:2]])}

На "как дела":
{chr(10).join(['  ' + ex for ex in status_examples[:2]])}

На "что делаешь":
{chr(10).join(['  ' + ex for ex in action_examples[:2]])}

=== КРИТИЧЕСКИЕ ПРАВИЛА ===

1. Отвечай КОРОТКО - одна-две фразы максимум
2. Будь {tone_desc}
3. Используй факты о себе только когда релевантно
4. НЕ выходи за рамки своего стиля
5. Помни контекст предыдущих сообщений
6. ЗАПРЕЩЕНО: странные фразы, противоречия, нечеловеческие ответы
7. Заканчивай пунктуацией: {main_punct}
"""
    
    return system_prompt

def analyze_and_build_smart():
    """Главная функция анализа"""
    try:
        with open('data/facts_advanced.json', 'r', encoding='utf-8') as f:
            facts = json.load(f)
    except FileNotFoundError:
        print("❌ facts_advanced.json не найден!")
        facts = {'personal': {}, 'location': {}, 'hobbies': {}, 'social': {}, 'beliefs': {}}
    
    # ChromaDB
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        collection = client.get_collection(name="user_messages", embedding_function=embedding_function)
        all_docs = collection.get(include=['documents', 'embeddings'])
        messages = all_docs.get('documents', [])
    except Exception as e:
        print(f"⚠️ ChromaDB ошибка: {e}")
        messages = []
    
    print(f"📊 Анализирую {len(messages)} сообщений...")
    
    # Извлекаем компоненты
    style_features = extract_style_features(messages)
    print(f"✅ Стиль: {len(style_features['sentence_starts'])} примеров")
    
    tone_markers = extract_tone_markers(messages)
    print(f"✅ Тон: {[t for t, _ in tone_markers[:2]]}")
    
    response_patterns = extract_response_patterns(messages)
    print(f"✅ Паттерны найдены")
    
    # Создаем промт
    system_prompt = build_smart_system_prompt(facts, style_features, tone_markers, response_patterns)
    
    # Сохраняем
    template = {
        "system_prompt": system_prompt,
        "style_analysis": {
            "sentence_starts": [s for s, _ in style_features['sentence_starts']],
            "tone": [t for t, _ in tone_markers],
            "avg_length": style_features['avg_sentence_length'],
            "response_patterns": response_patterns
        },
        "created_at": __import__('datetime').datetime.now().isoformat()
    }
    
    with open('data/prompt_template.json', 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print("\n✅ Анализ завершен!")
    return template

def load_prompt_template():
    """Загружает шаблон"""
    try:
        with open('data/prompt_template.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ prompt_template.json не найден! Запусти analyze_and_build_smart()")
        return None

if __name__ == "__main__":
    template = analyze_and_build_smart()
