@echo off
chcp 65001 > nul
echo ================================
echo 🤖 ГИБРИДНЫЙ ЗАПУСК RAG AI-КЛОНА
echo ================================
echo Структура: Скрипты в /backend, Docker в корне
echo.

REM 1. Переходим в корневую папку проекта
cd /d "%~dp0"
echo 📁 Текущая папка: %CD%

REM 2. Сбор данных на хосте (из папки backend)
echo.
echo 1. 🔍 Сбор данных из Telegram на хосте...
cd backend
python 1_collect_data.py
if errorlevel 1 (
    echo ❌ Ошибка сбора данных
    pause
    exit /b 1
)
cd ..

REM 3. Запуск Docker
echo.
echo 2. 🐳 Запуск Docker контейнеров...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Ошибка Docker
    echo Проверьте: docker --version и docker-compose --version
    pause
    exit /b 1
)

REM Даем Docker время на запуск
timeout /t 5 /nobreak > nul

REM 4. Построение векторной БД в контейнере
echo.
echo 3. 🗄️  Построение векторной базы данных...
docker-compose exec rag-ai-clone python build_vector_db_fixed.py
if errorlevel 1 (
    echo ⚠️  Ошибка при построении БД, продолжаем...
)

REM 5. Генерация промта в контейнере
echo.
echo 4. 📝 Генерация промта...
docker-compose exec rag-ai-clone python style_analyzer_smart.py
if errorlevel 1 (
    echo ⚠️  Ошибка при генерации промта, продолжаем...
)

REM 6. Запуск бота в фоне
echo.
echo 5. 🤖 Запуск Telegram бота...
docker-compose exec -d rag-ai-clone python 3_telegram_bot.py

REM 7. Проверка
echo.
echo 6. 🔍 Проверка работоспособности...
docker-compose exec rag-ai-clone python -c "
import json
import os
print('✅ Проверка файлов в контейнере:')
files = ['data/user_messages.json', 'data/prompt_template.json', 'data/facts_advanced.json']
for f in files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        print(f'   {f}: {size} байт')
    else:
        print(f'   {f}: ❌ не найден')
"

echo.
echo ================================
echo ✅ ВСЁ ГОТОВО!
echo ================================
echo.
echo 🤖 Telegram бот запущен в Docker
echo 📝 Чтобы увидеть логи: docker-compose logs -f rag-ai-clone
echo 🛑 Чтобы остановить: docker-compose down
echo.
pause