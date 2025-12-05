# Makefile для RAG AI проекта

.PHONY: help setup collect build generate run test clean docker-up docker-down

help:
	@echo "🤖 RAG AI Telegram Clone - Команды:"
	@echo ""
	@echo "  make setup      - Установка зависимостей"
	@echo "  make collect    - Сбор данных из Telegram (шаг 1)"
	@echo "  make build      - Построение векторной БД (шаг 2)"
	@echo "  make generate   - Генерация промпта (шаг 3)"
	@echo "  make run        - Запуск бота (шаг 4)"
	@echo "  make all        - Запуск всех шагов"
	@echo "  make test       - Запуск тестов"
	@echo "  make clean      - Очистка данных"
	@echo "  make docker-up  - Запуск в Docker"
	@echo "  make docker-down- Остановка Docker"
	@echo ""

setup:
	pip install -r requirements.txt

collect:
	python 1_collect_data.py

build:
	python build_vector_db_fixed.py

generate:
	python style_analyzer_smart.py

run:
	python 3_telegram_bot.py

all: collect build generate run

test:
	python -m pytest tests/ -v

clean:
	rm -rf data/*.json
	rm -rf data/chroma_db
	rm -f *.log

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-shell:
	docker exec -it rag-ai-app /bin/bash