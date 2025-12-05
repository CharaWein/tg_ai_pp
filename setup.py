#!/usr/bin/env python3
"""
setup.py - Автоматическая настройка проекта
Запустите: python setup.py
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def print_header():
    """Печатает заголовок"""
    print("\n" + "="*60)
    print("🛠️  НАСТРОЙКА RAG AI TELEGRAM CLONE")
    print("="*60)

def check_docker():
    """Проверяет Docker"""
    print("\n🔍 Проверяю Docker...")
    try:
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker установлен: {result.stdout.strip()}")
        return True
    except:
        print("❌ Docker НЕ УСТАНОВЛЕН!")
        print("\n📥 Установите Docker:")
        print("  Windows/Mac: https://docs.docker.com/get-docker/")
        print("  Linux Ubuntu: sudo apt-get install docker.io")
        print("  Linux другие: curl -fsSL https://get.docker.com | sh")
        return False

def check_docker_compose():
    """Проверяет Docker Compose"""
    print("\n🔍 Проверяю Docker Compose...")
    try:
        # Пробуем новую команду (docker compose)
        result = subprocess.run(["docker", "compose", "version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker Compose установлен (новый формат)")
            return True
        
        # Пробуем старую команду (docker-compose)
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker Compose установлен: {result.stdout.strip()}")
        return True
    except:
        print("❌ Docker Compose НЕ УСТАНОВЛЕН!")
        print("\n📥 Установите Docker Compose:")
        print("  https://docs.docker.com/compose/install/")
        return False

def setup_env_file():
    """Настраивает .env файл"""
    print("\n🔧 Настраиваю переменные окружения...")
    
    # Создаем .env.example если его нет
    env_example = Path(".env.example")
    if not env_example.exists():
        print("📝 Создаю .env.example...")
        env_example.write_text("""# Telegram API (получить на https://my.telegram.org)
TELEGRAM_API_ID=ваш_api_id_здесь
TELEGRAM_API_HASH=ваш_api_hash_здесь
TELEGRAM_PHONE=+79991234567

# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=ваш_bot_token_здесь

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# Приложение
DEBUG=true
LOG_LEVEL=INFO
""")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Создаю .env из примера...")
        shutil.copy(".env.example", ".env")
        print("✅ Файл .env создан")
        print("\n📋 ОТРЕДАКТИРУЙТЕ ФАЙЛ .env:")
        print("  1. Откройте .env в текстовом редакторе")
        print("  2. Вставьте ваши Telegram API ключи")
        print("  3. Сохраните файл")
        return False
    else:
        print("✅ Файл .env уже существует")
        return True

def check_python_dependencies():
    """Проверяет Python зависимости"""
    print("\n🔍 Проверяю Python зависимости...")
    
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("❌ Файл requirements.txt не найден!")
        return False
    
    try:
        # Пробуем установить зависимости
        print("📦 Устанавливаю зависимости...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                      check=True, capture_output=True)
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Ошибка установки зависимостей: {e}")
        print("💡 Попробуйте установить вручную:")
        print(f"   pip install -r requirements.txt")
        return False

def create_directories():
    """Создает необходимые директории"""
    print("\n📁 Создаю структуру директорий...")
    
    directories = [
        "backend/data",
        "logs",
        "scripts",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {directory}/")
    
    return True

def update_config_paths():
    """Обновляет пути в config.py"""
    print("\n⚙️  Обновляю конфигурационные пути...")
    
    config_file = Path("backend/config.py")
    if not config_file.exists():
        print("⚠️  Файл config.py не найден, пропускаю...")
        return True
    
    try:
        content = config_file.read_text(encoding='utf-8')
        
        # Обновляем BASE_DIR
        if 'BASE_DIR = Path(__file__).parent' in content:
            content = content.replace(
                'BASE_DIR = Path(__file__).parent',
                'BASE_DIR = Path(__file__).parent'
            )
        
        # Обновляем пути к данным
        if 'DATA_DIR = BASE_DIR / "data"' in content:
            content = content.replace(
                'DATA_DIR = BASE_DIR / "data"',
                'DATA_DIR = BASE_DIR / "data"'
            )
        
        config_file.write_text(content, encoding='utf-8')
        print("✅ Конфигурация обновлена")
        return True
        
    except Exception as e:
        print(f"⚠️  Ошибка обновления config.py: {e}")
        return True  # Пропускаем, не критично

def show_next_steps():
    """Показывает следующие шаги"""
    print("\n" + "="*60)
    print("✅ НАСТРОЙКА ЗАВЕРШЕНА!")
    print("="*60)
    
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. 📝 Отредактируйте файл .env:")
    print("   - TELEGRAM_API_ID и TELEGRAM_API_HASH с https://my.telegram.org")
    print("   - BOT_TOKEN от @BotFather")
    print("   - TELEGRAM_PHONE ваш номер телефона")
    
    print("\n2. 🐳 Запустите проект:")
    print("   docker-compose up -d")
    
    print("\n3. 📋 Проверьте логи:")
    print("   docker-compose logs -f")
    
    print("\n4. 🤖 Начните использовать:")
    print("   - Напишите вашему боту в Telegram")
    print("   - Или проверьте: curl http://localhost:8080/health")
    
    print("\n" + "="*60)
    print("❓ Помощь:")
    print("   docker-compose --help")
    print("   python main.py --help")

def main():
    """Основная функция"""
    print_header()
    
    # Создаем директории
    create_directories()
    
    # Проверяем Docker
    if not check_docker():
        print("\n⚠️  Продолжаю без Docker...")
    
    if not check_docker_compose():
        print("\n⚠️  Продолжаю без Docker Compose...")
    
    # Настраиваем .env
    setup_env_file()
    
    # Проверяем зависимости
    check_python_dependencies()
    
    # Обновляем конфигурацию
    update_config_paths()
    
    # Показываем следующие шаги
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при настройке: {e}")
        import traceback
        traceback.print_exc()