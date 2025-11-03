import json
import os

def check_training_data(user_id: str):
    """Детальная проверка тренировочных данных"""
    data_path = f"user_data/{user_id}/training_data_alpaca.json"
    
    print(f"🔍 Детальная проверка данных для user_id: {user_id}")
    
    if not os.path.exists(data_path):
        print("❌ Файл данных не найден!")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Всего примеров: {len(data)}")
    
    # Анализ качества данных
    valid_examples = 0
    total_length = 0
    empty_outputs = 0
    
    for i, item in enumerate(data):
        if isinstance(item, dict) and item.get('output'):
            output = item['output'].strip()
            if len(output) > 5:  # Минимальная длина осмысленного ответа
                valid_examples += 1
                total_length += len(output)
            else:
                empty_outputs += 1
    
    print(f"✅ Валидных примеров: {valid_examples}/{len(data)}")
    print(f"📏 Средняя длина ответа: {total_length/max(valid_examples, 1):.1f} символов")
    print(f"❌ Пустых ответов: {empty_outputs}")
    
    # Покажем несколько реальных примеров
    print(f"\n🔍 Примеры данных (первые 3):")
    for i, item in enumerate(data[:3]):
        if isinstance(item, dict):
            print(f"\n📝 Пример {i+1}:")
            print(f"   Инструкция: {item.get('instruction', 'N/A')[:50]}...")
            print(f"   Вход: {item.get('input', 'N/A')[:50]}...")
            print(f"   Выход: {item.get('output', 'N/A')[:100]}...")

if __name__ == "__main__":
    user_id = "6209265331"
    check_training_data(user_id)