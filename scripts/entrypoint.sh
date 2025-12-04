#!/bin/bash
set -e

echo "🤖 RAG AI Telegram Clone - Entrypoint"
echo "======================================"

# Проверяем Ollama
check_ollama() {
    echo "🔍 Проверяю Ollama подключение..."
    
    COUNTER=0
    MAX_ATTEMPTS=30
    
    while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
        if curl -s $OLLAMA_API_URL/api/tags > /dev/null 2>&1; then
            echo "✅ Ollama доступна"
            
            # Проверяем модель
            if curl -s $OLLAMA_API_URL/api/tags | grep -q $OLLAMA_MODEL; then
                echo "✅ Модель $OLLAMA_MODEL найдена"
                return 0
            else
                echo "❌ Модель $OLLAMA_MODEL не найдена"
                echo "💡 Запусти: ollama pull $OLLAMA_MODEL"
                return 1
            fi
        else
            COUNTER=$((COUNTER + 1))
            echo "  Попытка $COUNTER/$MAX_ATTEMPTS..."
            sleep 5
        fi
    done
    
    echo "❌ Не удалось подключиться к Ollama"
    return 1
}

# Создаем папки если нужно
mkdir -p /app/backend/data /app/logs

# Проверяем Ollama
if ! check_ollama; then
    exit 1
fi

echo ""
echo "🚀 Запускаю проект..."
echo ""

# Запускаем главный скрипт
exec python run.py "$@"