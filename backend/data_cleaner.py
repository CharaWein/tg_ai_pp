# data_cleaner.py
import json
import re
import os
from typing import List, Dict

def ultra_clean_training_data(user_id: str = "6209265331"):
    """Сверхтщательная очистка данных для обучения"""
    data_file = f"user_data/{user_id}/training_data.json"
    
    with open(data_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    print(f"📝 До очистки: {len(messages)} сообщений")
    
    cleaned_messages = []
    removed_count = 0
    
    for msg in messages:
        if isinstance(msg, dict):
            text = msg.get('text', '').strip()
            
            # Жесткая фильтрация
            if not is_high_quality_text(text):
                removed_count += 1
                continue
            
            # Нормализация текста
            text = normalize_text(text)
            msg['text'] = text
            cleaned_messages.append(msg)
    
    print(f"✅ После очистки: {len(cleaned_messages)} сообщений")
    print(f"🗑️ Удалено: {removed_count} сообщений")
    
    # Сохраняем очищенные данные
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_messages, f, ensure_ascii=False, indent=2)
    
    return cleaned_messages

def is_high_quality_text(text: str) -> bool:
    """Проверка текста на высокое качество"""
    if not text or len(text) < 10 or len(text) > 500:
        return False
    
    # Проверка русского языка
    russian_ratio = check_russian_ratio(text)
    if russian_ratio < 0.6:
        return False
    
    # Проверка на мусор
    if contains_gibberish(text):
        return False
    
    # Проверка на повторения
    if has_repetitions(text):
        return False
    
    # Проверка на специальные символы
    if re.search(r'[{}[\]<>|\\]', text):
        return False
    
    return True

def check_russian_ratio(text: str) -> float:
    """Проверяет процент русских символов в тексте"""
    russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
    total_chars = len(re.sub(r'\s', '', text))
    
    if total_chars == 0:
        return 0
    
    return russian_chars / total_chars

def normalize_text(text: str) -> str:
    """Нормализация текста"""
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Нормализуем кавычки
    text = re.sub(r'[«»""]', '"', text)
    
    # Убираем множественные знаки препинания
    text = re.sub(r'([!?])\1+', r'\1', text)
    
    return text

def contains_gibberish(text: str) -> bool:
    """Проверка на бессмысленный текст"""
    # Слишком много повторяющихся символов
    if re.search(r'(.)\1{4,}', text):
        return True
    
    # Слишком много специальных символов
    special_chars = len(re.findall(r'[^\w\sа-яА-ЯёЁ.,!?;:\-\'"()]', text))
    if special_chars / len(text) > 0.1:
        return True
    
    return False

def has_repetitions(text: str) -> bool:
    """Проверка на повторяющиеся слова"""
    words = text.lower().split()
    if len(words) < 3:
        return False
    
    word_counts = {}
    for word in words:
        if len(word) > 3:
            word_counts[word] = word_counts.get(word, 0) + 1
            if word_counts[word] > 3:
                return True
    
    return False

# Альтернативная функция для обратной совместимости
def clean_non_russian_data(user_id: str = "6209265331"):
    """Удаляем все не-русские сообщения (старая версия)"""
    return ultra_clean_training_data(user_id)

if __name__ == "__main__":
    ultra_clean_training_data()