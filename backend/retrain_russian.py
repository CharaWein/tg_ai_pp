# retrain_russian.py
import os
import shutil
from lora_trainer_advanced import AdvancedLoraTrainer
import json

def retrain_with_russian_model():
    """Переобучение на русской модели"""
    user_id = "6209265331"
    
    print("🔄 Переобучение на русской модели...")
    
    # Загружаем данные
    with open(f"user_data/{user_id}/training_data.json", 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    # Удаляем старую модель (английскую)
    model_path = f"trained_models/user_{user_id}"
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
        print("🗑️ Удалена старая английская модель")
    
    # Обучаем на русской модели
    trainer = AdvancedLoraTrainer(model_name="sberbank-ai/rugpt3small_based_on_gpt2")
    trainer.load_model()
    
    results = trainer.train_quick_lora(messages, model_path)
    
    print(f"✅ Переобучение завершено!")
    print(f"📊 Loss: {results['train_loss']:.4f}")
    print(f"📝 Примеров: {results['samples_processed']}")
    
    return results

if __name__ == "__main__":
    retrain_with_russian_model()