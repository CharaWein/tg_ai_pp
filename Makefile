# Makefile для управления проектом

.PHONY: help build build-dev up up-dev down logs clean test collect build-db analyze run-bot all

# Цвета для вывода
GREEN=\033[0;32m
NC=\033[0m

help: ## Показать эту справку
	@echo "$(GREEN)🤖 RAG AI Telegram Clone - Команды управления$(NC)"
	@echo ""
	@echo "📦 Docker команды:"
	@echo "  $(GREEN)make build$(NC)     - Собрать production образ"
	@echo "  $(GREEN)make build-dev$(NC) - Собрать development образ"
	@echo "  $(GREEN)make up$(NC)        - Запустить production"
	@echo "  $(GREEN)make up-dev$(NC)    - Запустить development"
	@echo "  $(GREEN)make down$(NC)      - Остановить все контейнеры"
	@echo "  $(GREEN)make logs$(NC)      - Показать логи"
	@echo "  $(GREEN)make clean$(NC)     - Очистить всё"
	@echo ""
	@echo "🚀 Команды проекта:"
	@echo "  $(GREEN)make build-db$(NC)  - Построение векторной БД"
	@echo "  $(GREEN)make analyze$(NC)   - Анализ стиля"
	@echo "  $(GREEN)make run-bot$(NC)   - Запуск Telegram бота"
	@echo "  $(GREEN)make all$(NC)       - Весь пайплайн"
	@echo "  $(GREEN)make test$(NC)      - Запуск тестов"
	@echo ""
	@echo "🔄 CI/CD команды:"
	@echo "  $(GREEN)make ci-test$(NC)   - Запустить CI тесты"
	@echo "  $(GREEN)make ci-build$(NC)  - Сборка для CI"
	@echo "  $(GREEN)make ci-push$(NC)   - Отправить образ в registry"

# Docker команды
build: ## Собрать production образ
	docker-compose -f docker-compose.yml build

build-dev: ## Собрать development образ
	docker-compose -f docker-compose.dev.yml build

up: ## Запустить production
	docker-compose -f docker-compose.prod.yml up -d

up-dev: ## Запустить development
	docker-compose -f docker-compose.dev.yml up -d

down: ## Остановить все контейнеры
	docker-compose -f docker-compose.yml down || true
	docker-compose -f docker-compose.dev.yml down || true
	docker-compose -f docker-compose.prod.yml down || true

logs: ## Показать логи
	docker-compose -f docker-compose.yml logs -f

clean: ## Полная очистка
	make down
	docker system prune -a -f --volumes
	rm -rf backend/data/* logs/*

# Команды проекта (запускаются внутри контейнера)

build-db: ## Построение векторной БД
	docker-compose -f docker-compose.dev.yml exec rag-ai-app python build_vector_db_fixed.py

analyze: ## Анализ стиля
	docker-compose -f docker-compose.dev.yml exec rag-ai-app python style_analyzer_smart.py

run-bot: ## Запуск Telegram бота
	docker-compose -f docker-compose.dev.yml exec rag-ai-app python 3_telegram_bot.py

all: ## Весь пайплайн
	@echo "$(GREEN)🚀 Запускаю весь пайплайн...$(NC)"
	@echo ""
	@echo "2. Построение векторной БД..."
	make build-db || (echo "❌ Ошибка построения БД"; exit 1)
	@echo ""
	@echo "3. Анализ стиля..."
	make analyze || (echo "❌ Ошибка анализа стиля"; exit 1)
	@echo ""
	@echo "4. Запуск Telegram бота..."
	make run-bot || (echo "❌ Ошибка запуска бота"; exit 1)
	@echo ""
	@echo "$(GREEN)✅ Весь пайплайн успешно завершен!$(NC)"

test: ## Запуск тестов
	docker-compose -f docker-compose.dev.yml exec rag-ai-app python -m pytest tests/ -v

# CI/CD команды
ci-test: ## Запустить CI тесты
	docker build -t rag-ai-test -f Dockerfile .
	docker run --rm rag-ai-test python -m pytest tests/ -v

ci-build: ## Сборка для CI
	docker build -t yourusername/rag-ai-clone:${TAG} -f Dockerfile .
	docker tag yourusername/rag-ai-clone:${TAG} yourusername/rag-ai-clone:latest

ci-push: ## Отправить образ в registry
	echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin
	docker push yourusername/rag-ai-clone:${TAG}
	docker push yourusername/rag-ai-clone:latest