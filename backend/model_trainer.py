# model_trainer.py
import os
import json
import torch
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from torch.utils.data import Dataset
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDataset(Dataset):
    def __init__(self, tokenizer, data, max_length=256):
        self.tokenizer = tokenizer
        self.data = data
        self.max_length = max_length
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        # Создаем текстовый пример в формате диалога
        if item.get('input'):
            text = f"Вопрос: {item['input']}\nОтвет: {item['output']}"
        else:
            text = f"Инструкция: {item['instruction']}\nОтвет: {item['output']}"
        
        # Токенизация
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }

class RussianModelTrainer:
    """Тренер для русских моделей с исправлениями"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        
        # ТОЛЬКО РУССКИЕ И ПРОВЕРЕННЫЕ МОДЕЛИ
        self.available_models = [
            "sberbank-ai/rugpt3small_based_on_gpt2",  # Русская, стабильная
            "tinkoff-ai/ruDialoGPT-small",           # Русская диалоговая
            "ai-forever/rugpt3small_based_on_gpt2",  # Альтернативная русская
        ]
    
    def load_model(self, model_index: int = 0):
        """Загрузка модели с приоритетом на русские модели"""
        try:
            if model_index >= len(self.available_models):
                logger.error("❌ Все русские модели недоступны")
                return False
                
            model_name = self.available_models[model_index]
            logger.info(f"🔄 Загружаем модель: {model_name}")
            
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Загружаем модель
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            logger.info(f"✅ Модель {model_name} успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели {model_name}: {e}")
            
            # Очищаем память
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            # Пробуем следующую модель
            if model_index + 1 < len(self.available_models):
                logger.info("🔄 Пробуем следующую модель...")
                return self.load_model(model_index + 1)
            else:
                logger.error("❌ Все модели недоступны")
                return False
    
    def train_model(self, user_id: str, training_data: list) -> dict:
        """Основное обучение модели"""
        try:
            import time
            start_time = time.time()
            
            # Проверяем данные
            if len(training_data) < 10:
                return {
                    "success": False,
                    "message": f"Недостаточно данных: {len(training_data)} примеров (нужно минимум 10)",
                    "training_time": 0,
                    "samples_used": 0
                }
            
            # Загружаем модель
            if not self.load_model():
                return {
                    "success": False,
                    "message": "Не удалось загрузить модель",
                    "training_time": 0,
                    "samples_used": 0
                }
            
            logger.info(f"✅ Модель загружена: {self.tokenizer.name_or_path}")
            
            # Ограничиваем данные для стабильности
            limited_data = training_data[:500]  # Максимум 500 примеров
            logger.info(f"📊 Используем {len(limited_data)} примеров для обучения")
            
            # Создаем датасет
            dataset = SimpleDataset(self.tokenizer, limited_data)
            
            # Параметры обучения
            training_args = TrainingArguments(
                output_dir=f"trained_models/user_{user_id}",
                overwrite_output_dir=True,
                num_train_epochs=2,
                per_device_train_batch_size=2,
                gradient_accumulation_steps=2,
                warmup_steps=50,
                logging_steps=20,
                save_steps=100,
                learning_rate=3e-5,
                weight_decay=0.01,
                fp16=torch.cuda.is_available(),
                remove_unused_columns=False,
                report_to=None,
                save_total_limit=1,
                dataloader_drop_last=True,
            )
            
            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False,
            )
            
            # Тренер
            trainer = Trainer(
                model=self.model,
                args=training_args,
                data_collator=data_collator,
                train_dataset=dataset,
                tokenizer=self.tokenizer,
            )
            
            # Обучаем
            logger.info("🚀 Начинаем обучение...")
            trainer.train()
            
            # Сохраняем
            trainer.save_model()
            self.tokenizer.save_pretrained(f"trained_models/user_{user_id}")
            
            training_time = time.time() - start_time
            
            return {
                "success": True,
                "message": f"Модель успешно обучена на {len(limited_data)} примерах",
                "model_path": f"trained_models/user_{user_id}",
                "training_time": round(training_time, 2),
                "samples_used": len(limited_data),
                "base_model": self.tokenizer.name_or_path,
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения: {e}")
            return {
                "success": False,
                "message": f"Ошибка обучения: {str(e)}",
                "training_time": 0,
                "samples_used": 0
            }

def train_user_model(user_id: str) -> dict:
    """Функция для запуска обучения извне"""
    try:
        # Загружаем данные
        data_path = f"user_data/{user_id}/training_data_alpaca.json"
        if not os.path.exists(data_path):
            return {
                "success": False,
                "message": "Данные для обучения не найдены"
            }
        
        with open(data_path, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        # Запускаем обучение
        trainer = RussianModelTrainer()
        result = trainer.train_model(user_id, training_data)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }

if __name__ == "__main__":
    # Тестирование
    user_id = "6209265331"
    result = train_user_model(user_id)
    print(f"Результат: {result}")