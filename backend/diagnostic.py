# diagnostic.py - ДИАГНОСТИКА ПРОБЛЕМЫ С EMPTY ANSWERS
# Скрипт для проверки каждого компонента системы

import os
import sys
import json
import requests
from pathlib import Path

print("\n" + "=" * 70)
print("🔍 ДИАГНОСТИКА RAG AI-КЛОНА")
print("=" * 70 + "\n")

# ========== ШАГИ ДИАГНОСТИКИ ==========

# ШАГИ 1: Проверка config.py
print("[1️⃣] Проверка CONFIG.PY")
print("-" * 70)
try:
    from config import BOT_TOKEN, OLLAMA_API_URL, OLLAMA_MODEL, DEBUG
    print(f"✅ Config загружен")
    print(f"   BOT_TOKEN: {'***' if BOT_TOKEN else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"   OLLAMA_API_URL: {OLLAMA_API_URL}")
    print(f"   OLLAMA_MODEL: {OLLAMA_MODEL}")
    print(f"   DEBUG: {DEBUG}")
except Exception as e:
    print(f"❌ Ошибка загрузки config: {e}")
    sys.exit(1)

# ШАГИ 2: Проверка OLLAMA подключения
print("\n[2️⃣] Проверка OLLAMA ПОДКЛЮЧЕНИЯ")
print("-" * 70)
try:
    resp = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
    if resp.status_code == 200:
        models = resp.json().get('models', [])
        print(f"✅ OLLAMA запущена!")
        print(f"   Установленные модели:")
        for model in models:
            model_name = model.get('name', 'Unknown')
            print(f"   - {model_name}")
        
        # Проверяем нужную модель
        if any(OLLAMA_MODEL in m.get('name', '') for m in models):
            print(f"   ✅ Модель {OLLAMA_MODEL} найдена!")
        else:
            print(f"   ❌ Модель {OLLAMA_MODEL} НЕ НАЙДЕНА!")
            print(f"      Запусти: ollama pull {OLLAMA_MODEL.split(':')[0]}")
    else:
        print(f"❌ OLLAMA ответила с кодом {resp.status_code}")
except requests.ConnectionError:
    print(f"❌ НЕ МОГУ ПОДКЛЮЧИТЬСЯ К OLLAMA")
    print(f"   Убедись что OLLAMA запущена: ollama serve")
    print(f"   URL: {OLLAMA_API_URL}")
except Exception as e:
    print(f"❌ Ошибка проверки OLLAMA: {e}")

# ШАГИ 3: Проверка файлов данных
print("\n[3️⃣] Проверка ФАЙЛОВ ДАННЫХ")
print("-" * 70)
files_to_check = [
    'data/user_messages.json',
    'data/facts_advanced.json',
    'data/prompt_template.json',
    'data/dialogue_history.json'
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"✅ {file_path} ({size} байт)")
    else:
        print(f"❌ {file_path} НЕ НАЙДЕН")

# ШАГИ 4: Проверка prompt_template
print("\n[4️⃣] Проверка PROMPT TEMPLATE")
print("-" * 70)
try:
    with open('data/prompt_template.json', 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    system_prompt = template.get('system_prompt', '')
    if system_prompt:
        print(f"✅ Prompt загружен ({len(system_prompt)} символов)")
        print(f"   Первые 200 символов:")
        print(f"   {system_prompt[:200]}...")
    else:
        print(f"❌ Prompt пустой!")
except Exception as e:
    print(f"❌ Ошибка загрузки prompt: {e}")

# ШАГИ 5: Тестовый запрос к OLLAMA
print("\n[5️⃣] ТЕСТОВЫЙ ЗАПРОС К OLLAMA")
print("-" * 70)
try:
    test_data = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Ты Андрей. Отвечай кратко."
            },
            {
                "role": "user",
                "content": "Привет"
            }
        ],
        "stream": False,
        "temperature": 0.7
    }
    
    print(f"Отправляю запрос на {OLLAMA_API_URL}/api/chat...")
    resp = requests.post(
        f"{OLLAMA_API_URL}/api/chat",
        json=test_data,
        timeout=30
    )
    
    if resp.status_code == 200:
        result = resp.json()
        answer = result.get('message', {}).get('content', '')
        if answer:
            print(f"✅ OLLAMA ответила!")
            print(f"   Ответ: {answer[:100]}...")
        else:
            print(f"❌ OLLAMA вернула пустой ответ")
            print(f"   Полный ответ: {result}")
    else:
        print(f"❌ OLLAMA ошибка {resp.status_code}")
        print(f"   {resp.text[:200]}")
except Exception as e:
    print(f"❌ Ошибка при тестовом запросе: {e}")

# ШАГИ 6: Проверка llm_generator_final.py
print("\n[6️⃣] Проверка LLM GENERATOR")
print("-" * 70)
try:
    from llm_generator_final import generator
    print(f"✅ llm_generator_final загружен")
    
    # Проверяем есть ли ChromaDB collection
    if generator.collection:
        print(f"✅ ChromaDB collection найдена")
        count = generator.collection.count()
        print(f"   Документов в базе: {count}")
    else:
        print(f"⚠️ ChromaDB collection не найдена")
    
    # Проверяем prompt_template
    if generator.prompt_template:
        print(f"✅ Prompt template загружен")
    else:
        print(f"❌ Prompt template НЕ ЗАГРУЖЕН")
except Exception as e:
    print(f"❌ Ошибка загрузки generator: {e}")

# ШАГИ 7: Проверка clean_answer функции
print("\n[7️⃣] ПРОВЕРКА CLEAN_ANSWER ФИЛЬТРАЦИИ")
print("-" * 70)
try:
    test_answers = [
        "Привет! Как дела?",
        "Я не человек, я ассистент",
        "Привет",
        "Норм, всё кодю",
        "я помощник ai"
    ]
    
    for test_answer in test_answers:
        cleaned = generator.clean_answer(test_answer)
        status = "✅ ПРОШЁЛ" if cleaned else "❌ ОТФИЛЬТРОВАН"
        print(f"{status}: '{test_answer}' -> '{cleaned}'")
except Exception as e:
    print(f"❌ Ошибка при тестировании clean_answer: {e}")

# ШАГИ 8: Итоговый результат
print("\n" + "=" * 70)
print("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
print("=" * 70 + "\n")

print("""
ЕСЛИ ВСЁ ✅ - ПРОБЛЕМА В OLLAMA ОТВЕТЕ или CLEAN_ANSWER

ВОЗМОЖНЫЕ РЕШЕНИЯ:

1️⃣ ЕСЛИ OLLAMA НЕ ЗАПУЩЕНА:
   ollama serve

2️⃣ ЕСЛИ МОДЕЛЬ НЕ УСТАНОВЛЕНА:
   ollama pull dolphin-mixtral

3️⃣ ЕСЛИ ОТВЕТЫ ФИЛЬТРУЮТСЯ:
   Проверь bad_patterns в llm_generator_final.py
   Может быть слишком строгая фильтрация

4️⃣ ЕСЛИ ВСЕ ОТВЕТЫ ПУСТЫЕ:
   Добавь DEBUG логирование в generate_answer()
   Посмотри какой ответ приходит от OLLAMA до фильтрации

════════════════════════════════════════════════════════════════════════════
""")
