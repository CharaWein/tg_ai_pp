import subprocess
import sys
import os
import threading
import time

def start_backend():
    """Запуск бэкенд сервера"""
    print("🚀 Запуск бэкенд сервера...")
    # Добавляем путь к backend в Python path
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_dir)
    
    try:
        # Импортируем и запускаем сервер
        from clone_server import app
        import uvicorn
        print("✅ Бэкенд сервер успешно загружен")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("🔍 Проверьте наличие всех файлов в папке backend/")
    except Exception as e:
        print(f"❌ Ошибка запуска бэкенда: {e}")

def setup_directories():
    """Создание необходимых директорий"""
    directories = ['backend/trained_models', 'backend/user_data', 'frontend/src']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✅ Директории созданы")

if __name__ == "__main__":
    print("🤖 Запуск AI Clone Project...")
    
    # Создаем необходимые директории
    setup_directories()
    
    # Запускаем бэкенд
    start_backend()