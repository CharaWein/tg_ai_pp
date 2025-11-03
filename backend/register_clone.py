import requests
import sys

def register_clone(user_id: str, clone_name: str = None):
    """Регистрация клона через API"""
    if clone_name is None:
        clone_name = f"AI Клон пользователя {user_id}"
    
    try:
        response = requests.post(
            "http://localhost:8001/clone/register",
            params={"user_id": user_id, "clone_name": clone_name}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Клон успешно зарегистрирован!")
            print(f"🔗 Токен: {result['token']}")
            print(f"🌐 Веб-интерфейс: {result['web_url']}")
            return result['token']
        else:
            print(f"❌ Ошибка: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python register_clone.py <user_id> [clone_name]")
        sys.exit(1)
    
    user_id = sys.argv[1]
    clone_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    register_clone(user_id, clone_name)