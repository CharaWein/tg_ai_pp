# test_ollama_direct.py
# Прямой тест Ollama БЕЗ всей системы

import requests
import json
from config import OLLAMA_API_URL, OLLAMA_MODEL

print("=" * 60)
print("🔍 ДИАГНОСТИКА OLLAMA")
print("=" * 60)

# Тест 1: Соединение с Ollama
print("\n[Тест 1] Проверка соединения с Ollama...")
try:
    resp = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=5)
    if resp.status_code == 200:
        models = resp.json().get('models', [])
        print(f"✅ Ollama работает!")
        print(f"   Доступные модели: {[m.get('name', 'unknown') for m in models]}")
        
        # Проверяем нужную модель
        model_names = [m.get('name', '') for m in models]
        if any(OLLAMA_MODEL in name for name in model_names):
            print(f"   ✅ {OLLAMA_MODEL} загружена")
        else:
            print(f"   ⚠️  {OLLAMA_MODEL} НЕ найдена!")
    else:
        print(f"❌ Ошибка: статус {resp.status_code}")
except Exception as e:
    print(f"❌ Ошибка соединения: {e}")
    print(f"   Проверь: Ollama запущена на {OLLAMA_API_URL}?")
    print(f"   Команда: ollama serve")
    exit(1)

# Тест 2: Простой вопрос БЕЗ системного промта
print(f"\n[Тест 2] Простой вопрос к {OLLAMA_MODEL}...")
simple_data = {
    "model": OLLAMA_MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Привет! Ответь одним словом."
        }
    ],
    "stream": False
}

try:
    resp = requests.post(
        f"{OLLAMA_API_URL}/api/chat",
        json=simple_data,
        timeout=60
    )
    if resp.status_code == 200:
        result = resp.json()
        answer = result.get('message', {}).get('content', '').strip()
        print(f"✅ Модель отвечает!")
        print(f"   Ответ: {answer}")
    else:
        print(f"❌ Ошибка: статус {resp.status_code}")
        print(f"   Response: {resp.text}")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")

# Тест 3: С системным промтом
print(f"\n[Тест 3] Вопрос с системным промтом...")
system_data = {
    "model": OLLAMA_MODEL,
    "messages": [
        {
            "role": "system",
            "content": "Ты помощник. Отвечай кратко."
        },
        {
            "role": "user",
            "content": "Как дела?"
        }
    ],
    "stream": False,
    "temperature": 0.58
}

try:
    resp = requests.post(
        f"{OLLAMA_API_URL}/api/chat",
        json=system_data,
        timeout=60
    )
    if resp.status_code == 200:
        result = resp.json()
        answer = result.get('message', {}).get('content', '').strip()
        print(f"✅ Модель отвечает с промтом!")
        print(f"   Ответ: {answer}")
    else:
        print(f"❌ Ошибка: статус {resp.status_code}")
        print(f"   Response: {resp.text}")
except Exception as e:
    print(f"❌ Ошибка запроса: {e}")

# Тест 4: Проверка prompt_template.json
print(f"\n[Тест 4] Проверка prompt_template.json...")
try:
    with open('data/prompt_template.json', 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    system_prompt = template.get('system_prompt', '')
    print(f"✅ prompt_template.json загружен")
    print(f"   Размер system_prompt: {len(system_prompt)} символов")
    
    if 'ПРИМЕРЫ' in system_prompt:
        print(f"   ✅ Примеры найдены в system_prompt")
    else:
        print(f"   ⚠️  Примеры НЕ найдены")
    
    if 'привет' in system_prompt.lower():
        print(f"   ✅ Примеры приветствий есть")
    else:
        print(f"   ⚠️  Примеров приветствий нет")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")

print("\n" + "=" * 60)
print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 60)
print("\nЕсли все тесты прошли ✅ — проблема в llm_generator.py структуре JSON")
print("Если тесты не прошли ❌ — проблема в самой Ollama или конфиге")
