# data_cleaner.py
import json
import re
import os
from langdetect import detect, LangDetectError

def clean_non_russian_data():
    """Удаляем все не-русские сообщения"""
    user_id = "6209265331"
    data_file = f"user_data/{user_id}/training_data.json"
    
    with open(data_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    print(f"📝 До очистки: {len(messages)} сообщений")
    
    cleaned_messages = []
    removed_count = 0
    
    for msg in messages:
        if isinstance(msg, dict):
            text = msg.get('text', '').strip()
            
            # Пропускаем пустые сообщения
            if not text or len(text) < 3:
                removed_count += 1
                continue
            
            # Проверяем русский язык (простой метод)
            russian_ratio = check_russian_text(text)
            
            # Оставляем только сообщения с >60% русских символов
            if russian_ratio > 0.6:
                cleaned_messages.append(msg)
            else:
                removed_count += 1
                print(f"🗑️ Удалено (не русский): {text[:50]}...")
    
    print(f"✅ После очистки: {len(cleaned_messages)} сообщений")
    print(f"🗑️ Удалено: {removed_count} сообщений")
    
    # Сохраняем очищенные данные
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_messages, f, ensure_ascii=False, indent=2)
    
    return cleaned_messages

def check_russian_text(text):
    """Проверяет процент русских символов в тексте"""
    # Считаем русские буквы
    russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
    total_chars = len(re.sub(r'\s', '', text))  # Игнорируем пробелы
    
    if total_chars == 0:
        return 0
    
    return russian_chars / total_chars

if __name__ == "__main__":
    # Установи библиотеку для определения языка если нужно:
    # pip install langdetect
    clean_non_russian_data()