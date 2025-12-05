#!/usr/bin/env python3
"""
main.py - Главный скрипт запуска RAG AI Telegram Clone
Запускает все шаги автоматически
"""

import sys
import os
import subprocess
from pathlib import Path

# Добавляем backend в путь Python
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def check_environment():
    """Проверяет окружение"""
    print("🔍 Проверяю окружение...")
    
    # Проверяем наличие backend папки
    if not Path("backend").exists():
        print("❌ Папка 'backend/' не найдена!")
        return False
    
    # Проверяем необходимые файлы
    required_files = [
        "backend/config.py",
        "backend/1_collect_data.py",
        "backend/build_vector_db_fixed.py",
        "backend/style_analyzer_smart.py",
        "backend/3_telegram_bot.py",
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    print("✅ Окружение проверено")
    return True

def run_step(step_number, script_name, description):
    """Запускает один шаг пайплайна"""
    print(f"\n{'='*60}")
    print(f"🚀 Шаг {step_number}: {description}")
    print(f"{'='*60}")
    
    script_path = Path("backend") / script_name
    
    if not script_path.exists():
        print(f"❌ Скрипт {script_name} не найден!")
        return False
    
    try:
        # Запускаем скрипт из backend папки
        # Используем только имя файла, так как cwd установлен в "backend"
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd="backend"  # Запускаем из папки backend
        )
        
        if result.returncode == 0:
            print(f"✅ {description} завершен успешно")
            if result.stdout:
                # Показываем последние строки вывода
                lines = result.stdout.strip().split('\n')
                if len(lines) > 5:
                    print("📋 Вывод (последние 5 строк):")
                    for line in lines[-5:]:
                        print(f"  {line}")
                else:
                    print("📋 Вывод:")
                    for line in lines:
                        print(f"  {line}")
            return True
        else:
            print(f"❌ {description} завершился с ошибкой")
            print(f"Код ошибки: {result.returncode}")
            if result.stderr:
                print("Ошибка:")
                for line in result.stderr.strip().split('\n')[-10:]:
                    print(f"  {line}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при запуске {script_name}: {e}")
        return False

def run_full_pipeline():
    """Запускает полный пайплайн"""
    steps = [
        ("1_collect_data.py", "Сбор данных из Telegram"),
        ("build_vector_db_fixed.py", "Построение векторной БД"),
        ("style_analyzer_smart.py", "Генерация промпта"),
        ("3_telegram_bot.py", "Запуск Telegram бота")
    ]
    
    for i, (script, description) in enumerate(steps, 1):
        if not run_step(i, script, description):
            print(f"\n❌ Пайплайн остановлен на шаге {i}")
            return False
    
    return True

def run_bot_only():
    """Запускает только Telegram бота"""
    print("\n" + "="*60)
    print("🤖 Запуск только Telegram бота")
    print("="*60)
    
    try:
        # Импортируем и запускаем бота напрямую
        from backend import telegram_bot
        telegram_bot.main()
    except ImportError as e:
        print(f"❌ Не могу импортировать модуль: {e}")
        print("💡 Запускаю через subprocess...")
        
        # Используем только имя файла, так как cwd установлен в "backend"
        subprocess.run([sys.executable, "3_telegram_bot.py"], cwd="backend")

def main():
    """Основная функция"""
    print("\n" + "="*60)
    print("🤖 RAG AI TELEGRAM CLONE - ГЛАВНОЕ МЕНЮ")
    print("="*60)
    
    # Проверяем окружение
    if not check_environment():
        sys.exit(1)
    
    # Определяем режим запуска
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            # Полный пайплайн
            if run_full_pipeline():
                print("\n🎉 ВСЕ ШАГИ УСПЕШНО ВЫПОЛНЕНЫ!")
            else:
                print("\n❌ ПАЙПЛАЙН ЗАВЕРШИЛСЯ С ОШИБКАМИ")
                sys.exit(1)
        elif sys.argv[1] == "--bot":
            # Только бот
            run_bot_only()
        elif sys.argv[1] == "--docker":
            # Режим для Docker (автоматически определяет)
            print("🐳 Запуск в Docker режиме...")
            # Проверяем есть ли уже данные
            data_file = Path("backend/data/user_messages.json")
            if data_file.exists():
                print("✅ Данные уже собраны, запускаю только бота")
                run_bot_only()
            else:
                print("📊 Данных нет, запускаю полный пайплайн")
                run_full_pipeline()
        elif sys.argv[1] == "--help":
            print_help()
        else:
            print(f"❌ Неизвестный аргумент: {sys.argv[1]}")
            print_help()
    else:
        # Интерактивный режим
        print("\nВыберите режим запуска:")
        print("  1. Полный пайплайн (сбор данных + бот)")
        print("  2. Только Telegram бот")
        print("  3. Только сбор данных")
        print("  4. Выход")
        
        try:
            choice = input("\nВаш выбор (1-4): ").strip()
            
            if choice == "1":
                if run_full_pipeline():
                    print("\n🎉 ВСЕ ШАГИ УСПЕШНО ВЫПОЛНЕНЫ!")
            elif choice == "2":
                run_bot_only()
            elif choice == "3":
                run_step(1, "1_collect_data.py", "Сбор данных из Telegram")
            elif choice == "4":
                print("\n👋 До свидания!")
            else:
                print("❌ Неверный выбор")
        except KeyboardInterrupt:
            print("\n\n🛑 Завершено пользователем")

def print_help():
    """Показывает справку"""
    print("\nИспользование:")
    print("  python main.py [опция]")
    print("\nОпции:")
    print("  --full    : Запустить полный пайплайн (сбор данных + бот)")
    print("  --bot     : Запустить только Telegram бота")
    print("  --docker  : Автоматический режим для Docker")
    print("  --help    : Показать эту справку")
    print("\nПримеры:")
    print("  python main.py --full     # Полный запуск")
    print("  python main.py --bot      # Только бот")
    print("  python main.py            # Интерактивный режим")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Завершено пользователем")
    except Exception as e:
        print(f"\n❌ Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)