# register_clone.py
import json
import uuid
from datetime import datetime

def register_clone():
    """Принудительно регистрируем клона в сервере"""
    user_id = "6209265331"
    
    # Создаем токен
    token = str(uuid.uuid4())
    
    # Данные клона
    clone_data = {
        'user_id': user_id,
        'name': f"Клон пользователя {user_id}",
        'created_at': datetime.now().isoformat(),
        'active': True
    }
    
    # Загружаем существующие ссылки
    try:
        with open("clone_links.json", 'r', encoding='utf-8') as f:
            links = json.load(f)
    except:
        links = {}
    
    # Добавляем нашу ссылку
    links[token] = clone_data
    
    # Сохраняем
    with open("clone_links.json", 'w', encoding='utf-8') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Клон зарегистрирован!")
    print(f"🔗 Токен: {token}")
    print(f"👤 User ID: {user_id}")
    print(f"🌐 Ссылка: http://localhost:8001/clone/{token}/web")
    
    return token

if __name__ == "__main__":
    token = register_clone()