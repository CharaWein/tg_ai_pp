#!/bin/bash
# run.sh - скрипт запуска проекта

set -e  # Выход при ошибке

echo "🚀 Запуск RAG AI Telegram Clone..."
echo "📅 $(date)"
echo "📁 Рабочая директория: $(pwd)"

# Создаем необходимые директории
mkdir -p backend/data logs

# Проверяем, запускаем ли в Docker
if [ -f /.dockerenv ] || [ -f /run/.containerenv ]; then
    echo "🐳 Запуск в Docker контейнере"
    
    # Ждем Ollama
    echo "⏳ Ожидаю запуск Ollama..."
    sleep 10
    
    # Проверяем Ollama
    if curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama запущена"
    else
        echo "⚠️  Ollama не отвечает, пытаюсь запустить..."
        ollama serve &
        sleep 15
    fi
    
    # Загружаем модель если нужно
    echo "🤖 Проверяю модель Mistral..."
    if curl -s http://ollama:11434/api/tags | grep -q '"mistral:7b"'; then
        echo "✅ Модель Mistral уже загружена"
    else
        echo "⬇️  Загружаю модель Mistral 7B..."
        ollama pull mistral:7b || {
            echo "⚠️  Не удалось загрузить модель, продолжаю без неё"
        }
    fi
    
    # Запускаем основной скрипт в Docker режиме
    python main.py --docker
    
else
    echo "💻 Запуск на локальной машине"
    
    # Проверяем Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 не установлен!"
        exit 1
    fi
    
    # Проверяем зависимости
    if [ ! -f "backend/requirements.txt" ]; then
        echo "❌ Файл requirements.txt не найден!"
        exit 1
    fi
    
    # Определяем Python интерпретатор
    if [ -n "$VIRTUAL_ENV" ]; then
        # Если виртуальное окружение активировано, используем его python
        PYTHON_CMD="$VIRTUAL_ENV/bin/python"
        PIP_CMD="$VIRTUAL_ENV/bin/pip"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
    else
        echo "❌ Python3 не найден!"
        exit 1
    fi
    
    # Проверяем и устанавливаем зависимости
    echo "📦 Проверяю зависимости..."
    if ! $PYTHON_CMD -c "import telethon" 2>/dev/null; then
        echo "⚠️  Зависимости не установлены. Устанавливаю..."
        $PIP_CMD install -r backend/requirements.txt --quiet || {
            echo "❌ Ошибка установки зависимостей!"
            exit 1
        }
        echo "✅ Зависимости установлены"
    else
        echo "✅ Зависимости проверены"
    fi
    
    # Запускаем основной скрипт
    $PYTHON_CMD main.py "$@"
fi