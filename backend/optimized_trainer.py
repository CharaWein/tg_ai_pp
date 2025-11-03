# optimized_trainer.py
import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer, GPT2LMHeadModel
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset, DataLoader
import json
import os
import logging
from typing import List, Dict
import time
import re
from datetime import datetime
import numpy as np
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class UltraOptimizedDataset(Dataset):
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

class UltraOptimizedTrainer:
    def __init__(self, model_name: str = "sberbank-ai/rugpt3small_based_on_gpt2"):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🚀 Используется устройство: {self.device}")
        self.model = None
        self.tokenizer = None
        
    def load_model(self, model_path: str = None):
        """Сверхоптимизированная загрузка с LoRA"""
        try:
            logger.info("🔄 Загрузка модели с LoRA...")
            start_time = time.time()
            
            if model_path and os.path.exists(model_path):
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,  # Используем float32 для стабильности
                    device_map="auto"
                )
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            else:
                # Загрузка русскоязычной модели
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,  # float32 вместо float16 для стабильности
                    low_cpu_mem_usage=True,
                )
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
            # Критически важные настройки токенизатора
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Агрессивная LoRA конфигурация для быстрого обучения
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=16,  # Увеличим ранг
                lora_alpha=32,  # Увеличим alpha
                lora_dropout=0.1,
                target_modules=["c_attn", "c_proj", "c_fc", "wte", "wpe"],  # Добавим embedding слои
                bias="none"
            )
            
            self.model = get_peft_model(self.model, lora_config)
            self.model.to(self.device)
            
            # Включаем градиенты для всех обучаемых параметров
            self.model.train()
            for param in self.model.parameters():
                if param.requires_grad:
                    param.requires_grad = True
            
            load_time = time.time() - start_time
            logger.info(f"✅ Модель загружена за {load_time:.1f}с")
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            total_params = sum(p.numel() for p in self.model.parameters())
            logger.info(f"📊 Обучаемых параметров: {trainable_params:,} из {total_params:,} ({trainable_params/total_params*100:.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            raise

    def create_smart_prompts(self, text: str) -> List[str]:
        """Умное создание промптов для обучения"""
        if not text or len(text.strip()) < 5:
            return []
            
        text = text.strip()
        prompts = []
        
        # Определяем тип сообщения и создаем соответствующие промпты
        if any(mark in text for mark in ['?', 'что', 'как', 'почему', 'когда']):
            prompts.extend([
                f"Вопрос: {text}\nОтвет:",
                f"Пользователь: {text}\nАссистент:",
                f"Человек: {text}\nAI:"
            ])
        elif len(text.split()) > 8:
            prompts.extend([
                f"Контекст: {text}\nПродолжение:",
                f"Сообщение: {text}\nОтвет:"
            ])
        else:
            prompts.extend([
                f"Пользователь: {text}\nАссистент:",
                f"Человек: {text}\nAI:",
                f"Диалог: {text}\nПродолжение:"
            ])
        
        return prompts

    def prepare_smart_data(self, training_data: List[Dict]) -> List[str]:
        """Умная подготовка данных с приоритетом на качество"""
        logger.info("🎯 Умная подготовка данных...")
        
        quality_texts = []
        processed_count = 0
        
        # Сначала собираем статистику по длине сообщений
        lengths = []
        for item in training_data:
            text = ""
            if isinstance(item, dict) and 'text' in item:
                text = item['text'].strip()
            elif isinstance(item, str):
                text = item.strip()
            
            if text and len(text) > 5:
                lengths.append(len(text))
        
        if lengths:
            avg_length = np.mean(lengths)
        else:
            avg_length = 50
        
        # Отбираем оптимальные сообщения
        for item in training_data[:800]:
            text = ""
            if isinstance(item, dict) and 'text' in item:
                text = item['text'].strip()
            elif isinstance(item, str):
                text = item.strip()
            
            # Умная фильтрация
            if (text and len(text) > 8 and len(text) < 300 and 
                not re.search(r'http[s]?://', text) and
                text.count('?') <= 3 and 
                self.calculate_quality_score(text) > 0.4):
                
                prompts = self.create_smart_prompts(text)
                quality_texts.extend(prompts)
                processed_count += 1
        
        # Дублируем лучшие примеры для лучшего обучения
        if len(quality_texts) < 200:
            multiplier = max(2, 200 // len(quality_texts))
            quality_texts = quality_texts * multiplier
        
        logger.info(f"📊 Отобрано {processed_count} качественных сообщений")
        logger.info(f"📝 Создано {len(quality_texts)} обучающих примеров")
        
        return quality_texts[:1000]

    def calculate_quality_score(self, text: str) -> float:
        """Оценка качества текста"""
        score = 0.0
        
        # Длина текста
        if 15 <= len(text) <= 250:
            score += 0.3
        
        # Русские символы
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        if russian_chars / len(text) > 0.6:
            score += 0.3
        
        # Разнообразие символов
        unique_chars = len(set(text))
        if unique_chars / len(text) > 0.5:
            score += 0.2
        
        # Отсутствие мусора
        if not re.search(r'[^\w\sа-яА-ЯёЁ.,!?;:\-\'"()]', text):
            score += 0.2
        
        return score

    def train_ultra_optimized(
        self, 
        training_data: List[Dict],
        model_save_path: str
    ):
        """Сверхоптимизированное обучение с исправлением градиентов"""
        logger.info("🚀 Запуск сверхоптимизированного обучения...")
        start_time = time.time()
        
        # Подготовка умных данных
        texts = self.prepare_smart_data(training_data)
        if len(texts) < 50:
            raise ValueError(f"Недостаточно качественных данных: {len(texts)} примеров")
            
        # Создаем датасет
        dataset = UltraOptimizedDataset(texts, self.tokenizer)
        
        # Оптимальные параметры для быстрого обучения
        training_args = {
            'num_train_epochs': 3,
            'early_stopping': True,
            'per_device_train_batch_size': 2,  # Уменьшили батч для стабильности
            'gradient_accumulation_steps': 8,  # Увеличили accumulation
            'learning_rate': 5e-4,  # Уменьшили LR для стабильности
            'warmup_ratio': 0.1,
            'weight_decay': 0.01,
            'max_grad_norm': 1.0,
        }
        
        # Создаем DataLoader
        train_loader = DataLoader(
            dataset, 
            batch_size=training_args['per_device_train_batch_size'],
            shuffle=True,
            num_workers=0,
            pin_memory=True
        )
        
        # Оптимизатор с правильными настройками
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=training_args['learning_rate'],
            weight_decay=training_args['weight_decay']
        )
        
        # Простой планировщик
        total_steps = len(train_loader) * training_args['num_train_epochs']
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, 
            T_max=total_steps
        )
        
        # Обучение
        train_losses = []
        best_loss = float('inf')
        
        logger.info(f"📊 Начинаем обучение на {len(texts)} примерах")
        logger.info(f"⚙️  Параметры: {training_args}")
        
        global_step = 0

        patience = 3  # Останавливаем если 2 шага подряд без улучшений
        best_loss = float('inf')
        patience_counter = 0

        for epoch in range(training_args['num_train_epochs']):
            epoch_start = time.time()
            self.model.train()  # Важно: включаем режим обучения
            
            # Убеждаемся, что градиенты включены
            for param in self.model.parameters():
                if param.requires_grad:
                    param.requires_grad = True
            
            total_loss = 0
            steps = 0
            
            for batch_idx, batch in enumerate(train_loader):
                # Move to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Обнуляем градиенты
                optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(
                    input_ids=batch['input_ids'],
                    attention_mask=batch['attention_mask'],
                    labels=batch['labels']
                )
                
                loss = outputs.loss
                
                # Проверяем что loss требует градиенты
                if not loss.requires_grad:
                    logger.warning("Loss не требует градиентов! Проверяем модель...")
                    # Принудительно включаем градиенты
                    loss.requires_grad = True
                
                # Gradient accumulation
                if training_args['gradient_accumulation_steps'] > 1:
                    loss = loss / training_args['gradient_accumulation_steps']
                
                # Backward pass
                loss.backward()
                
                # Step only on accumulation boundary
                if (batch_idx + 1) % training_args['gradient_accumulation_steps'] == 0:
                    # Gradient clipping
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), 
                        training_args['max_grad_norm']
                    )
                    optimizer.step()
                    scheduler.step()
                    optimizer.zero_grad()
                    global_step += 1
                
                total_loss += loss.item()
                steps += 1
                
                # Логирование прогресса каждые 10 шагов
                if batch_idx % 10 == 0:
                    current_loss = total_loss / (steps + 1e-8)
                    current_lr = scheduler.get_last_lr()[0]
                    logger.info(f'Epoch {epoch+1}, Step {batch_idx}, Loss: {current_loss:.4f}, LR: {current_lr:.2e}')
            
            # Final gradient update if needed
            if steps % training_args['gradient_accumulation_steps'] != 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), training_args['max_grad_norm'])
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
            
            # Эпоха завершена
            avg_loss = total_loss / steps
            train_losses.append(avg_loss)
            
            epoch_time = time.time() - epoch_start
            logger.info(f"✅ Epoch {epoch+1}/{training_args['num_train_epochs']} - Loss: {avg_loss:.4f} - Time: {epoch_time:.1f}s")
            
            # Сохраняем лучшую модель
            if avg_loss < best_loss:
                best_loss = avg_loss
                self.save_model(model_save_path + "_best")
                logger.info(f"💾 Сохранена лучшая модель (loss: {best_loss:.4f})")

            #ранняя остановка
            if avg_loss < best_loss:
                best_loss = avg_loss
                patience_counter = 0
                self.save_model(model_save_path + "_best")
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print("🛑 Ранняя остановка - достигнут оптимум")
                    break
        
        # Загружаем лучшую модель
        if os.path.exists(model_save_path + "_best"):
            self.model = None  # Очищаем память
            self.load_model(model_save_path + "_best")
        
        self.save_model(model_save_path)
        
        total_time = time.time() - start_time
        logger.info(f"🎉 Обучение завершено за {total_time/60:.1f} минут!")
        logger.info(f"📈 Final loss: {best_loss:.4f}")
        
        return {
            'train_losses': train_losses,
            'final_epoch': len(train_losses),
            'best_loss': best_loss,
            'total_time': total_time,
            'training_examples': len(texts)
        }

    def save_model(self, save_path: str):
        """Эффективное сохранение модели"""
        os.makedirs(save_path, exist_ok=True)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        
        # Сохраняем информацию о тренировке
        training_info = {
            'saved_at': datetime.now().isoformat(),
            'model_type': 'rugpt3_lora_ultra_optimized',
            'trainable_parameters': sum(p.numel() for p in self.model.parameters() if p.requires_grad),
            'total_parameters': sum(p.numel() for p in self.model.parameters())
        }
        
        with open(os.path.join(save_path, 'training_info.json'), 'w') as f:
            json.dump(training_info, f, indent=2)
        
        logger.info(f"💾 Модель сохранена в {save_path}")

    def generate_response(self, message: str) -> str:
        """Оптимизированная генерация ответов"""
        try:
            self.model.eval()  # Переключаем в режим оценки
            
            prompt = f"Пользователь: {message}\nАссистент:"
            
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=128, truncation=True)
            inputs = inputs.to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=len(inputs[0]) + 60,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    top_p=0.85,
                    top_k=40,
                    early_stopping=True
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем ответ
            if "Ассистент:" in response:
                response = response.split("Ассистент:")[-1].strip()
            elif "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()
            else:
                response = response.replace(prompt, "").strip()
            
            # Очистка ответа
            response = re.sub(r'^\s*[:\-]\s*', '', response)
            
            return response if response and len(response) > 2 else "Расскажите подробнее!"
            
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            return "Давайте поговорим о чем-нибудь интересном!"

# Простая версия для обратной совместимости
class OptimizedTrainer(UltraOptimizedTrainer):
    """Совместимость со старым кодом"""
    def train_optimized(self, training_data, model_save_path):
        return self.train_ultra_optimized(training_data, model_save_path)