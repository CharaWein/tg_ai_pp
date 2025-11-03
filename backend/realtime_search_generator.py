# realtime_search_generator.py
import torch
import re
import os
import json
import numpy as np
from typing import List, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM

class RealtimeSearchGenerator:
    def __init__(self, model, tokenizer, user_id: str):
        self.model = model
        self.tokenizer = tokenizer
        self.user_id = user_id
        self.knowledge = self.load_knowledge()

    def load_knowledge(self) -> dict:
        """Загружает базу знаний с сообщениями"""
        knowledge_path = f"user_data/{self.user_id}/knowledge_base.json"
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    print(f"📚 Загружено {len(knowledge.get('all_messages', []))} сообщений для поиска")
                    return knowledge
            except Exception as e:
                print(f"❌ Ошибка загрузки знаний: {e}")
        return {"personal_info": {}, "interests": [], "all_messages": []}

    def generate_response(self, message: str) -> str:
        """Генерация с real-time поиском фактов"""
        # Сначала пытаемся найти точный ответ через поиск по ключевым словам
        keyword_answer = self.enhanced_keyword_search(message)
        if keyword_answer and self.is_good_answer(keyword_answer):
            print(f"🔍 Умный поиск нашел ответ: {keyword_answer}")
            return keyword_answer
        
        # Если поиск не сработал, генерируем обычным способом
        return self.fallback_generation(message)

    def enhanced_keyword_search(self, question: str) -> str:
        """Улучшенный поиск ответа по ключевым словам"""
        question_lower = question.lower()
        all_messages = self.knowledge.get("all_messages", [])
        
        if not all_messages:
            return ""
        
        # Улучшенные ключевые слова для разных типов вопросов
        keyword_groups = {
            'имя': {
                'keywords': ['зовут', 'имя', 'как тебя', 'представься', 'твое имя'],
                'response_patterns': ['меня зовут', 'мое имя', 'я -', 'зовите меня'],
                'extract_patterns': [
                    r'меня зовут\s+([А-Я][а-я]{2,})',
                    r'мое имя\s+([А-Я][а-я]{2,})',
                    r'я\s+([А-Я][а-я]{2,})',
                    r'зовите меня\s+([А-Я][а-я]{2,})'
                ]
            },
            'город': {
                'keywords': ['город', 'живешь', 'откуда', 'где живешь', 'местожительство'],
                'response_patterns': ['живу в', 'город', 'из города', 'в городе'],
                'extract_patterns': [
                    r'живу в\s+([А-Я][а-я]+)',
                    r'город\s+([А-Я][а-я]+)',
                    r'из\s+([А-Я][а-я]+)',
                    r'в\s+([А-Я][а-я]+)\s+живу'
                ]
            },
            'возраст': {
                'keywords': ['лет', 'возраст', 'сколько лет', 'возраст тебе'],
                'response_patterns': ['мне лет', 'возраст', 'мне год', 'лет'],
                'extract_patterns': [
                    r'мне\s+(\d{1,2})\s+лет',
                    r'возраст\s+(\d{1,2})',
                    r'(\d{1,2})\s+год'
                ]
            },
            'интересы': {
                'keywords': ['интерес', 'увлекаешься', 'хобби', 'нравится', 'любишь'],
                'response_patterns': ['нравится', 'люблю', 'увлекаюсь', 'интересуюсь'],
                'extract_patterns': [
                    r'нравится\s+([^.,!?]+)',
                    r'люблю\s+([^.,!?]+)',
                    r'увлекаюсь\s+([^.,!?]+)',
                    r'интересуюсь\s+([^.,!?]+)'
                ]
            },
            'работа': {
                'keywords': ['работа', 'профессия', 'занимаешься', 'учусь', 'делом'],
                'response_patterns': ['работаю', 'учусь', 'занимаюсь', 'профессия'],
                'extract_patterns': [
                    r'работаю\s+([^.,!?]+)',
                    r'учусь\s+([^.,!?]+)',
                    r'занимаюсь\s+([^.,!?]+)'
                ]
            },
            'друзья': {
                'keywords': ['друг', 'друзья', 'общаешься', 'знаком', 'подруг'],
                'response_patterns': ['друг', 'друзья', 'знаком', 'общаюсь'],
                'extract_patterns': [
                    r'друг\s+([А-Я][а-я]{2,})',
                    r'друзья\s+([А-Я][а-я]{2,})',
                    r'знаком\s+([А-Я][а-я]{2,})'
                ]
            }
        }
        
        # Определяем категорию вопроса
        question_category = None
        for category, data in keyword_groups.items():
            if any(keyword in question_lower for keyword in data['keywords']):
                question_category = category
                break
        
        if not question_category:
            return ""
        
        # Ищем релевантные сообщения
        relevant_messages = []
        response_patterns = keyword_groups[question_category]['response_patterns']
        
        for msg in all_messages:
            msg_lower = msg.lower()
            # Ищем сообщения, которые содержат ответные паттерны
            if any(pattern in msg_lower for pattern in response_patterns):
                relevant_messages.append(msg)
        
        # Если нашли релевантные сообщения, формируем ответ
        if relevant_messages:
            return self.construct_smart_answer(question, relevant_messages[:3], question_category, keyword_groups[question_category]['extract_patterns'])
        
        return ""
    
    def contains_gibberish(self, text: str) -> bool:
        """Проверяет текст на бессмыслицу"""
        if len(text) < 5:
            return True
        
        # Проверяем повторяющиеся символы
        if re.search(r'(.)\1{3,}', text):
            return True
        
        # Проверяем соотношение русских букв
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        total_chars = max(len(re.findall(r'\w', text)), 1)
        
        if russian_chars / total_chars < 0.5:
            return True
        
        # Проверяем на отсутствие смысловых слов
        meaningful_words = ['привет', 'как', 'что', 'где', 'когда', 'почему', 'да', 'нет', 'хорошо', 'спасибо']
        text_lower = text.lower()
        if not any(word in text_lower for word in meaningful_words):
            return len(text) > 30  # Длинный текст без смысловых слов = бред
        
        return False

    def construct_smart_answer(self, question: str, messages: List[str], category: str, extract_patterns: List[str]) -> str:
        """Умное построение ответа на основе найденных сообщений"""
        # Извлекаем ключевую информацию из сообщений
        extracted_info = self.extract_info_from_messages(messages, extract_patterns)
        
        if not extracted_info:
            # Если не нашли по паттернам, используем первое релевантное сообщение
            response = self.clean_context_response(messages[0])
        else:
            # Формируем естественный ответ
            answer_templates = {
                'имя': [
                    "Меня зовут {info}",
                    "Я {info}",
                    "Мое имя - {info}"
                ],
                'город': [
                    "Я живу в {info}",
                    "Мой город - {info}",
                    "Я из {info}"
                ],
                'возраст': [
                    "Мне {info} лет",
                    "Мой возраст - {info}",
                    "Мне {info}"
                ],
                'интересы': [
                    "Я увлекаюсь {info}",
                    "Мне нравится {info}",
                    "Мои интересы: {info}"
                ],
                'работа': [
                    "Я занимаюсь {info}",
                    "Моя работа связана с {info}",
                    "Я работаю в сфере {info}"
                ],
                'друзья': [
                    "У меня есть друзья: {info}",
                    "Я общаюсь с {info}",
                    "Мои друзья: {info}"
                ]
            }
            
            templates = answer_templates.get(category, ["{info}"])
            import random
            template = random.choice(templates)
            response = template.format(info=extracted_info)
        
        # ОБЯЗАТЕЛЬНО ОБРЕЗАЕМ ДО ОДНОГО ПРЕДЛОЖЕНИЯ
        return self.force_single_sentence(response)

    def extract_info_from_messages(self, messages: List[str], patterns: List[str]) -> str:
        """Извлекает конкретную информацию из сообщений по паттернам"""
        combined_text = " ".join(messages)
        
        for pattern in patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Очищаем extracted от лишних слов
                cleaned = self.clean_extracted_info(extracted)
                if cleaned:
                    return cleaned
        
        # Если не нашли по паттернам, возвращаем наиболее релевантную часть
        if messages:
            return self.get_most_relevant_part(messages[0])
        
        return ""

    def clean_extracted_info(self, info: str) -> str:
        """Очищает извлеченную информацию"""
        # Удаляем лишние слова и фразы
        stop_phrases = ['что', 'который', 'когда', 'где', 'как', 'очень', 'просто']
        words = info.split()
        cleaned_words = [word for word in words if word.lower() not in stop_phrases]
        
        cleaned = ' '.join(cleaned_words)
        
        # Обрезаем до разумной длины
        if len(cleaned) > 50:
            cleaned = cleaned[:50] + "..."
        
        return cleaned

    def get_most_relevant_part(self, text: str) -> str:
        """Извлекает наиболее релевантную часть текста"""
        # Разбиваем на предложения и берем первое содержательное
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and not any(word in sentence.lower() for word in ['привет', 'пока', 'спасибо']):
                return sentence[:100].strip()
        
        return text[:80].strip()

    def clean_context_response(self, text: str) -> str:
        """Очистка ответа из контекста"""
        # Удаляем технические фразы и лишнее
        cleanup_patterns = [
            r'Человек:\s*',
            r'Ты:\s*',
            r'Assistant:\s*',
            r'User:\s*',
        ]
        
        cleaned = text
        for pattern in cleanup_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Обрезаем до разумной длины
        if len(cleaned) > 120:
            sentences = re.split(r'[.!?]', cleaned)
            if sentences:
                cleaned = sentences[0].strip() + '.'
        
        return cleaned

    def is_good_answer(self, answer: str) -> bool:
        """Проверяет, что ответ адекватный"""
        if not answer or len(answer) < 3:
            return False
        
        # Проверяем на бред
        if self.contains_gibberish(answer):
            return False
        
        bad_patterns = [
            'не знаю', 'не указано', 'не сказано', 'не упоминается',
            'нет информации', 'не могу', 'не найдено', '...', '??', '!!'
        ]
        
        if any(pattern in answer.lower() for pattern in bad_patterns):
            return False
        
        # Проверяем, что ответ не состоит только из знаков препинания
        if re.match(r'^[^\wа-яА-Я]*$', answer):
            return False
        
        return True

    def fallback_generation(self, message: str) -> str:
        """Обычная генерация если поиск не сработал с строгим контролем"""
        try:
            prompt = self.build_smart_prompt(message)
            
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt", 
                max_length=512,
                truncation=True
            )
            
            attention_mask = torch.ones_like(inputs)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    attention_mask=attention_mask,
                    max_length=len(inputs[0]) + 40,  # Укоротили максимальную длину
                    num_return_sequences=1,
                    temperature=0.8,  # Немного увеличили температуру для разнообразия
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.3,  # Увеличили штраф за повторения
                    no_repeat_ngram_size=3,  # Увеличили размер n-gram для избежания повторений
                    early_stopping=True,
                    top_p=0.9,
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            response = self.aggressive_cleaning(response)
            
            return response if response else "Интересно! Расскажи подробнее."
            
        except Exception as e:
            print(f"Ошибка генерации: {e}")
            return "Давай поговорим о чем-нибудь интересном!"

    def aggressive_cleaning(self, text: str) -> str:
        """Агрессивная очистка и обрезка до первого законченного предложения"""
        if not text:
            return ""
        
        # Удаляем все технические паттерны
        patterns = [
            r'Assistant\s*:?\s*',
            r'User\s*:?\s*',
            r'Человек\s*:?\s*', 
            r'Ты\s*:?\s*',
            r'Я\s+сказал\s+',
            r'Я\s+ответил\s+',
            r'Я\s+спросил\s+',
            r'потом\s+я\s+',
            r'затем\s+я\s+',
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Удаляем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # ОБРЕЗАЕМ ДО ПЕРВОГО ЗАКОНЧЕННОГО ПРЕДЛОЖЕНИЯ
        cleaned = self.force_single_sentence(cleaned)
        
        # Убедимся, что ответ не слишком длинный
        if len(cleaned) > 120:
            cleaned = cleaned[:120].strip()
            # Находим последнее законченное предложение в обрезанном тексте
            cleaned = self.force_single_sentence(cleaned)
        
        return cleaned

    def force_single_sentence(self, text: str) -> str:
        """Принудительно обрезает текст до первого законченного предложения"""
        if not text:
            return ""
        
        # Ищем конец первого предложения
        sentence_endings = ['.', '!', '?', '…']
        
        for i, char in enumerate(text):
            if char in sentence_endings:
                # Проверяем, что это действительно конец предложения
                if i == len(text) - 1 or text[i+1] in [' ', '\n', '"', '»']:
                    return text[:i+1].strip()
        
        # Если не нашли конец предложения, добавляем точку в подходящем месте
        if len(text) > 80:
            # Обрезаем до 80 символов и добавляем точку
            return text[:80].strip() + '...'
        elif len(text) > 20:
            # Просто добавляем точку
            return text.strip() + '.'
        else:
            # Слишком короткий текст, оставляем как есть
            return text.strip()

    def clean_response(self, text: str) -> str:
        """Очистка ответа с агрессивной обрезкой"""
        patterns = [
            r'Assistant\s*:?\s*',
            r'User\s*:?\s*',
            r'Человек\s*:?\s*', 
            r'Ты\s*:?\s*',
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # ПРИМЕНЯЕМ АГРЕССИВНУЮ ОБРЕЗКУ
        cleaned = self.force_single_sentence(cleaned)
        
        return cleaned

    def build_smart_prompt(self, user_message: str) -> str:
        """Строит промпт с базовой информацией"""
        personal_info = self.knowledge.get("personal_info", {})
        interests = self.knowledge.get("interests", [])
        habits = self.knowledge.get("habits", [])
        friends = self.knowledge.get("friends", {})
        
        persona_parts = []
        if name := personal_info.get("name"):
            persona_parts.append(f"Меня зовут {name}")
        if age := personal_info.get("age"):
            persona_parts.append(f"Мне {age} лет")
        if city := personal_info.get("city"):
            persona_parts.append(f"Живу в {city}")
        if interests:
            persona_parts.append(f"Интересы: {', '.join(interests[:3])}")
        if habits:
            persona_parts.append(f"Привычки: {', '.join(habits[:2])}")
        if friends:
            friend_names = list(friends.keys())[:2]
            persona_parts.append(f"Друзья: {', '.join(friend_names)}")
        
        persona = ". ".join(persona_parts) if persona_parts else "Я AI-клон, обученный на ваших сообщениях"
        
        prompt = f"""Отвечай естественно как человек.
        
{persona}

Человек: {user_message}
Ты:"""
        
        return prompt

    def clean_response(self, text: str) -> str:
        """Очистка ответа"""
        patterns = [
            r'Assistant\s*:?\s*',
            r'User\s*:?\s*',
            r'Человек\s*:?\s*', 
            r'Ты\s*:?\s*',
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned