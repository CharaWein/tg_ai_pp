# test_link.py
import requests

def test_link(token):
    """Тестируем конкретную ссылку"""
    base_url = "http://localhost:8001"
    
    print(f"🔗 Тестируем токен: {token}")
    
    try:
        # Проверяем информацию о клоне
        response = requests.get(f"{base_url}/clone/{token}")
        if response.status_code == 200:
            print(f"✅ Клон найден: {response.json()}")
        else:
            print(f"❌ Клон не найден: {response.status_code}")
            
        # Проверяем веб-интерфейс
        response = requests.get(f"{base_url}/clone/{token}/web")
        if response.status_code == 200:
            print("✅ Веб-интерфейс доступен")
        else:
            print(f"❌ Веб-интерфейс не доступен: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    # Замени на актуальный токен из register_clone.py
    test_link("b51c2457-4a50-41d6-a4fb-a87c45eacbdd")