# debug_clone_server.py
import requests
import json
import os

def debug_clone_server():
    print("🔍 Диагностика AI Clone Server...")
    
    # 1. Проверяем статус сервера
    try:
        response = requests.get("http://localhost:8001/status")
        print(f"✅ Сервер работает: {response.json()}")
    except:
        print("❌ Сервер не отвечает на порту 8001")
        return
    
    # 2. Проверяем все ссылки
    try:
        response = requests.get("http://localhost:8001/admin/links")
        links = response.json()
        print(f"📊 Всего ссылок: {len(links)}")
        for token, info in links.items():
            print(f"  - {token}: {info}")
    except Exception as e:
        print(f"❌ Ошибка получения ссылок: {e}")
    
    # 3. Проверяем существование модели
    user_id = "6209265331"
    model_path = f"trained_models/user_{user_id}"
    print(f"🔍 Проверяем модель для {user_id}:")
    print(f"  Путь: {model_path}")
    print(f"  Существует: {os.path.exists(model_path)}")
    
    if os.path.exists(model_path):
        files = os.listdir(model_path)
        print(f"  Файлы: {files}")
    
    # 4. Проверяем конкретный токен
    test_token = "a68eb254-b0c3-4af3-b2f7-b8e3ab51812a"
    print(f"🔍 Проверяем токен: {test_token}")
    try:
        response = requests.get(f"http://localhost:8001/clone/{test_token}")
        print(f"  Статус: {response.status_code}")
        if response.status_code == 200:
            print(f"  Данные: {response.json()}")
        else:
            print(f"  Ошибка: {response.text}")
    except Exception as e:
        print(f"  Ошибка: {e}")

if __name__ == "__main__":
    debug_clone_server()