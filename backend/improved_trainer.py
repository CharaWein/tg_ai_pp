# improved_trainer.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from torch.utils.data import Dataset, DataLoader
import json
import os
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CleanDataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=128):
        self.tokenizer = tokenizer
        self.texts = texts
        self.max_length = max_length
        
    def __len__(self):
        return len(self.texts)
        
    def __getitem__(self, idx):
        text = self.texts[idx]
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': encoding['input_ids'].flatten()
        }

class ImprovedTrainer:
    def __init__(self, model_name: str = "sberbank-ai/rugpt3small_based_on_gpt2"):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Используется устройство: {self.device}")
        self.model = None
        self.tokenizer = None
        
    def load_model(self, model_path: str = None):
        """Загрузка модели"""
        try:
            logger.info("🔄 Загрузка модели...")
            
            if model_path and os.path.exists(model_path):
                self.model = AutoModelForCausalLM.from_pretrained(model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            self.model.to(self.device)
            logger.info("✅ Модель загружена")
            
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
            raise

    def clean_text(self, text):
        """Очистка текста от ссылок и мусора"""
        # Удаляем URL
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        text = re.sub(r'\S+\.(com|ru|org|net)\S*', '', text)
        
        # Удаляем упоминания и хештеги
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def prepare_clean_data(self, training_data):
        """Подготовка очищенных данных"""
        texts = []
        
        # Используем ВСЕ сообщения (без ограничения 200)
        logger.info(f"🎯 Используем {len(training_data)} сообщений")
        
        # Создаем чистые пары вопрос-ответ
        for i in range(len(training_data) - 1):
            current_msg = self.extract_text(training_data[i])
            next_msg = self.extract_text(training_data[i + 1])
            
            # Очищаем от ссылок и мусора
            current_msg = self.clean_text(current_msg)
            next_msg = self.clean_text(next_msg)
            
            if (current_msg and next_msg and 
                len(current_msg) > 5 and len(next_msg) > 5 and
                self.is_russian_text(current_msg) and self.is_russian_text(next_msg)):
                
                dialog = f"Человек: {current_msg}\nAI: {next_msg}"
                texts.append(dialog)
        
        logger.info(f"📊 Создано {len(texts)} чистых диалогов")
        return texts

    def extract_text(self, item):
        """Извлечение текста"""
        if isinstance(item, dict):
            return item.get('text', '').strip()
        elif isinstance(item, str):
            return item.strip()
        return ""

    def is_russian_text(self, text):
        """Проверяет, является ли текст преимущественно русским"""
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        total_chars = len(re.sub(r'\s', '', text))
        
        if total_chars == 0:
            return False
            
        return (russian_chars / total_chars) > 0.6

    def train_improved(
        self, 
        training_data,
        model_save_path: str,
        epochs: int = 3,
        batch_size: int = 2,
        learning_rate: float = 5e-5
    ):
        """Улучшенное обучение с очищенными данными"""
        logger.info("🔄 Улучшенное обучение...")
        
        texts = self.prepare_clean_data(training_data)
        
        if not texts or len(texts) < 10:
            logger.warning("Мало чистых данных, используем обычные")
            texts = self.prepare_data(training_data)
        
        train_dataset = CleanDataset(texts, self.tokenizer)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        
        train_losses = []
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0
            batches = 0
            
            for batch in train_loader:
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs.loss
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                batches += 1
                
                if batches % 20 == 0:
                    logger.info(f'Epoch {epoch+1}, Batch {batches}, Loss: {loss.item():.4f}')
            
            if batches > 0:
                avg_loss = total_loss / batches
                train_losses.append(avg_loss)
                logger.info(f"✅ Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")
        
        self.save_model(model_save_path)
        
        return {
            'train_losses': train_losses,
            'final_epoch': epochs,
            'final_loss': train_losses[-1] if train_losses else 0.0
        }

    def prepare_data(self, training_data):
        """Резервный метод подготовки данных"""
        texts = []
        for i in range(len(training_data) - 1):
            current_msg = self.extract_text(training_data[i])
            next_msg = self.extract_text(training_data[i + 1])
            
            if current_msg and next_msg and len(current_msg) > 3 and len(next_msg) > 3:
                dialog = f"Человек: {current_msg}\nAI: {next_msg}"
                texts.append(dialog)
        
        return texts

    def save_model(self, save_path: str):
        """Сохранение модели"""
        os.makedirs(save_path, exist_ok=True)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        logger.info(f"💾 Модель сохранена в {save_path}")

def improved_retrain():
    """Улучшенное переобучение"""
    user_id = "6209265331"
    
    print("🔄 Улучшенное переобучение...")
    
    # Загружаем данные
    data_file = f"user_data/{user_id}/training_data.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    
    # Удаляем старую модель
    model_path = f"trained_models/user_{user_id}"
    if os.path.exists(model_path):
        import shutil
        shutil.rmtree(model_path)
        print("🗑️ Удалена старая модель")
    
    # Обучаем улучшенным методом
    trainer = ImprovedTrainer(model_name="sberbank-ai/rugpt3small_based_on_gpt2")
    trainer.load_model()
    results = trainer.train_improved(messages, model_path, epochs=4)
    
    print(f"✅ Переобучение завершено!")
    print(f"📊 Loss: {results['final_loss']:.4f}")
    print(f"🎯 Эпох: {results['final_epoch']}")
    
    return results

if __name__ == "__main__":
    improved_retrain()