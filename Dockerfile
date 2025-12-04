# Dockerfile.simple
FROM python:3.11-slim

WORKDIR /app

# Минимальные системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя сразу
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/backend/data /app/logs && \
    chown -R appuser:appuser /app

USER appuser

# Копируем зависимости
COPY --chown=appuser:appuser requirements.txt .

# Устанавливаем CPU-only PyTorch и остальное
RUN pip install --no-cache-dir --default-timeout=1000 \
    torch==2.2.2 \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Копируем код
COPY --chown=appuser:appuser backend/ ./backend/

WORKDIR /app/backend

ENTRYPOINT ["python", "run.py"]