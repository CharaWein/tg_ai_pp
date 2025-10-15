# simple_russian_generator.py
import torch
import re

class SimpleRussianGenerator:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer
        
    def generate_response(self, user_message: str) -> str:
        """Простая генерация на русском без лишних меток"""
        
        # ПРОСТОЙ промпт без "User/Assistant"
        prompt = f"{user_message}"
        
        inputs = self.tokenizer.encode(prompt, return_tensors="pt", max_length=64, truncation=True)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=len(inputs[0]) + 40,  # Короткие ответы
                num_return_sequences=1,
                temperature=0.3,  # НИЗКАЯ температура для предсказуемости
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=2.0,  # Сильный штраф за повторения
                no_repeat_ngram_size=3,
                top_p=0.7,
                top_k=20,
                early_stopping=True
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Удаляем оригинальный промпт из ответа
        response = response.replace(prompt, "").strip()
        
        # Очищаем ответ от мусора
        response = self.clean_response(response)
        
        return response if response else "Интересно! Расскажи подробнее."
    
    def clean_response(self, text: str) -> str:
        """Тщательная очистка ответа"""
        # Удаляем все упоминания Assistant/User и т.д.
        patterns = [
            r'Assistant\s*:?\s*',
            r'User\s*:?\s*', 
            r'Пользователь\s*:?\s*',
            r'Ассистент\s*:?\s*',
            r'<\|.*?\|>',
            r'[^\w\sа-яА-ЯёЁ.,!?;:\-\'"()]'  # Удаляем странные символы
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Проверяем на бессмыслицу
        if self.is_gibberish(cleaned):
            return ""
            
        return cleaned
    
    def is_gibberish(self, text: str) -> bool:
        """Проверка на бессмысленный текст"""
        if len(text) < 2:
            return True
            
        # Слишком много повторяющихся символов
        if re.search(r'(.)\1{3,}', text):
            return True
            
        # Слишком мало русских букв
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        if russian_chars / len(text) < 0.3:
            return True
            
        return False