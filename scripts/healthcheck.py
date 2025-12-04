#!/usr/bin/env python3
"""
Health check для Docker
"""

import os
import sys
import requests
from pathlib import Path

def check_health():
    """Проверяет здоровье приложения"""
    
    # Проверяем что необходимые файлы существуют
    required_files = [
        "data/user_messages.json",
        "data/facts_advanced.json", 
        "data/prompt_template.json"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            return False
    
    # Проверяем подключение к Ollama
    try:
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code != 200:
            return False
    except:
        return False
    
    return True

if __name__ == "__main__":
    if check_health():
        print("OK")
        sys.exit(0)
    else:
        print("UNHEALTHY")
        sys.exit(1)