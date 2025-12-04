#!/usr/bin/env python3
"""
Главный скрипт запуска проекта - управляет всем пайплайном
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
import logging

Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/app.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Запускает Python скрипт"""
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 {description}")
    logger.info(f"{'='*60}")
    
    if not Path(script_path).exists():
        logger.error(f"❌ Файл не найден: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 минут на выполнение
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} завершен")
            if result.stdout:
                logger.info(f"Вывод: {result.stdout[-500:]}")
            return True
        else:
            logger.error(f"❌ Ошибка в {description}")
            if result.stderr:
                logger.error(f"Ошибка: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Таймаут выполнения {description}")
        return False
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка: {e}")
        return False

def check_ollama():
    """Проверяет что Ollama доступна"""
    import requests
    
    ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    
    logger.info(f"🔍 Проверяю подключение к Ollama: {ollama_url}")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            # Проверяем модель
            model = os.getenv("OLLAMA_MODEL", "mistral:7b")
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            if any(model in name for name in model_names):
                logger.info(f"✅ Ollama доступна, модель {model} найдена")
                return True
            else:
                logger.error(f"❌ Модель {model} не найдена в Ollama")
                logger.info(f"Доступные модели: {model_names}")
                return False
        else:
            logger.error(f"❌ Ollama недоступна: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Ollama: {e}")
        logger.info("💡 Убедись что Ollama запущена: ollama serve")
        return False

def check_environment():
    """Проверяет необходимые переменные окружения"""
    required_vars = [
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "BOT_TOKEN",
        "TELEGRAM_PHONE"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
        logger.info("💡 Проверь .env файл")
        return False
    
    return True

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"\n🛑 Получен сигнал {signum}, завершаю работу...")
    sys.exit(0)

def main():
    """Главная функция запуска пайплайна"""
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("\n" + "="*60)
    logger.info("🤖 RAG AI TELEGRAM CLONE - ПАЙПЛАЙН ЗАПУСКА")
    logger.info("="*60)
    
    # Проверяем переменные окружения
    if not check_environment():
        sys.exit(1)
    
    # Проверяем Ollama
    if not check_ollama():
        sys.exit(1)
    
    # Создаем необходимые папки
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Определяем последовательность выполнения
    scripts = [
        ("build_vector_db_fixed.py", "Построение векторной базы данных"),
        ("style_analyzer_smart.py", "Анализ стиля и генерация промта"),
        ("3_telegram_bot.py", "Запуск Telegram бота")
    ]
    
    # Запускаем все скрипты последовательно
    for script, description in scripts:
        if not run_script(script, description):
            logger.error(f"\n❌ Пайплайн остановлен на: {description}")
            logger.info("💡 Проверь логи выше и исправь ошибку")
            sys.exit(1)
        
        # Небольшая пауза между скриптами
        time.sleep(2)
    
    logger.info("\n" + "="*60)
    logger.info("🎉 ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЕН!")
    logger.info("="*60)
    logger.info("\n🤖 Telegram бот запущен и работает")
    logger.info("📝 Пиши боту в Telegram!")
    logger.info("💡 Для остановки нажми Ctrl+C")
    
    # Держим скрипт запущенным (бот работает в фоне)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Бот остановлен пользователем")
        sys.exit(0)

if __name__ == "__main__":
    main()