# 🤖 RAG AI Telegram Clone (Docker без Ollama)

**Docker-версия, где Ollama устанавливается отдельно для гибкости**

[![Docker](https://img.shields.io/badge/Docker-✓-blue)](https://docker.com)
[![Ollama](https://img.shields.io/badge/Ollama-Separate-green)](https://ollama.ai)
[![Python](https://img.shields.io/badge/Python-3.11%2B-yellow)](https://python.org)

## 🚀 Быстрый старт (4 шага)

# Windows: скачай с https://ollama.com
# Linux/macOS:
curl -fsSL https://ollama.com/install.sh | sh

# Загрузи модель
ollama pull mistral:7b

Получение Telegram API ключей
1. Получи API ключи:
Перейди на my.telegram.org

Войди в свой аккаунт

Нажми "API Development Tools"

Создай новое приложение

Запиши:

api_id → TELEGRAM_API_ID

api_hash → TELEGRAM_API_HASH

Твой номер телефона → TELEGRAM_PHONE

2. Создай бота:
Найди @BotFather в Telegram

Отправь команду /newbot

Следуй инструкциям

Получи токен → BOT_TOKEN
# Скопируй пример конфигурации
Заполни .env файл:

в папке backend/data заполни о себе информацию в txt файле и удали остальные файлы если они есть

выполни команду:
docker-compose up --no-cache


# Запусти проект с помощью run.bat

