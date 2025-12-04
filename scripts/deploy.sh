#!/bin/bash
set -e

# Конфигурация
ENVIRONMENT=${1:-production}
IMAGE_TAG=${2:-latest}
CONFIG_FILE="docker-compose.$ENVIRONMENT.yml"

echo "🚀 Deploying RAG AI Clone ($ENVIRONMENT)..."

# Проверяем конфигурацию
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

# Создаем .env если нет
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file before deployment!"
    exit 1
fi

# Проверяем Ollama
echo "🔍 Checking Ollama..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running!"
    echo "💡 Start Ollama: ollama serve"
    exit 1
fi

# Pull образ
echo "📥 Pulling Docker image..."
docker-compose -f $CONFIG_FILE pull

# Останавливаем старый контейнер
echo "🛑 Stopping old container..."
docker-compose -f $CONFIG_FILE down || true

# Запускаем новый
echo "🚀 Starting new container..."
docker-compose -f $CONFIG_FILE up -d

# Проверяем здоровье
echo "🏥 Waiting for health check..."
sleep 30

if docker-compose -f $CONFIG_FILE ps | grep -q "healthy"; then
    echo "✅ Deployment successful!"
    
    # Показываем логи
    echo ""
    echo "📋 Container status:"
    docker-compose -f $CONFIG_FILE ps
    
    echo ""
    echo "📊 Recent logs:"
    docker-compose -f $CONFIG_FILE logs --tail=20
else
    echo "❌ Deployment failed!"
    docker-compose -f $CONFIG_FILE logs
    exit 1
fi