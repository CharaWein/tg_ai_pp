# clone_server.py
import os
import json
import logging
import sys
import re
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Dict, Any
try:
    from hybrid_knowledge_extractor import create_hybrid_knowledge_base
except ImportError:
    # Если все еще есть проблемы, создаем простую заглушку
    def create_hybrid_knowledge_base(user_id: str):
        return {
            "personal_info": {},
            "interests": [],
            "all_messages": [],
            "extraction_date": "2024-01-01",
            "extraction_method": "fallback"
        }

sys.path.append(os.path.dirname(__file__))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Clone Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class KnowledgeExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.raw_data_path = f"user_data/{user_id}/training_data.json"
        self.knowledge_path = f"user_data/{user_id}/knowledge_base.json"
        
    def extract_and_save_knowledge(self) -> bool:
        try:
            logger.info(f"🔄 Запускаем извлечение знаний для пользователя {self.user_id}")
            
            ai_extractor = SmartKnowledgeExtractor(self.user_id)
            
            # Вызываем правильный метод
            success = ai_extractor.extract_and_save_knowledge()
            
            if success:
                logger.info("✅ Знания успешно извлечены")
                return True
            else:
                logger.error("❌ Не удалось извлечь знания")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения знаний: {e}")
            return False


class KnowledgeBase:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.knowledge_path = f"user_data/{user_id}/knowledge_base.json"
        self.knowledge = self.load_knowledge()
        
    def load_knowledge(self) -> Dict[str, Any]:
        """Загружает структурированные знания из knowledge_base.json"""
        try:
            if not os.path.exists(self.knowledge_path):
                logger.warning(f"❌ Файл знаний не найден: {self.knowledge_path}")
                return {}
            
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                knowledge = json.load(f)
            
            logger.info(f"✅ Загружены знания для пользователя {self.user_id}")
            return knowledge
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки знаний: {e}")
            return {}
    
    def get_relevant_knowledge(self, user_message: str) -> str:
        """Возвращает релевантные знания для текущего сообщения"""
        message_lower = user_message.lower()
        relevant_facts = []
        
        # Проверяем упоминание имени
        if any(phrase in message_lower for phrase in ['как тебя зовут', 'твое имя', 'представься']):
            if name := self.knowledge.get("personal_info", {}).get("name"):
                relevant_facts.append(f"Меня зовут {name}")
        
        # Проверяем вопросы о возрасте
        if any(phrase in message_lower for phrase in ['сколько лет', 'твой возраст', 'возраст']):
            if age := self.knowledge.get("personal_info", {}).get("age"):
                relevant_facts.append(f"Мне {age} лет")
        
        # Проверяем вопросы о городе
        if any(phrase in message_lower for phrase in ['откуда', 'город', 'живешь']):
            if city := self.knowledge.get("personal_info", {}).get("city"):
                relevant_facts.append(f"Живу в {city}")
        
        # Проверяем вопросы о друзьях
        for friend in self.knowledge.get("friends", {}):
            if friend.lower() in message_lower:
                relevant_facts.append(f"Знаю {friend}")
        
        # Проверяем интересы
        for interest in self.knowledge.get("interests", []):
            if interest in message_lower:
                relevant_facts.append(f"Интересуюсь {interest}")
        
        return " | ".join(relevant_facts) if relevant_facts else ""

    def get_persona_description(self) -> str:
        """Возвращает описание личности для промпта"""
        persona_parts = []
        
        # Базовая информация
        personal_info = self.knowledge.get("personal_info", {})
        
        if name := personal_info.get("name"):
            persona_parts.append(f"Меня зовут {name}")
        
        if age := personal_info.get("age"):
            persona_parts.append(f"Мне {age} лет")
        
        if city := personal_info.get("city"):
            persona_parts.append(f"Живу в {city}")
        
        if work := personal_info.get("work"):
            persona_parts.append(f"Работаю: {work}")
        
        # Интересы
        if interests := self.knowledge.get("interests", [])[:5]:
            persona_parts.append(f"Интересы: {', '.join(interests)}")
        
        # Друзья
        if friends := list(self.knowledge.get("friends", {}).keys())[:3]:
            persona_parts.append(f"Друзья: {', '.join(friends)}")
        
        # Привычки
        if habits := self.knowledge.get("habits", [])[:3]:
            persona_parts.append(f"Привычки: {', '.join(habits)}")
        
        return ". ".join(persona_parts) if persona_parts else "Я - AI-клон, обученный на ваших сообщениях"

class AdvancedRussianGenerator:
    def __init__(self, model, tokenizer, user_id: str):
        self.model = model
        self.tokenizer = tokenizer
        self.user_id = user_id
        self.conversation_history = []
        self.knowledge_base = KnowledgeBase(user_id)
        
    def generate_response(self, user_id: str, message: str) -> str:
        """Генерация ответов с учетом качественных знаний"""
        try:
            if user_id not in self.models:
                if not self.load_user_model(user_id):
                    return "Привет! Рад общению!"
            
            from advanced_generator import AdvancedRussianGenerator
            
            generator = AdvancedRussianGenerator(self.models[user_id], self.tokenizers[user_id], user_id)
            
            # ВАЖНО: передаем только message, context не обязателен
            response = generator.generate_response(message)
            
            return response
                
        except Exception as e:
            logger.error(f"Ошибка генерации для {user_id}: {e}")
            import traceback
            logger.error(f"Подробности ошибки: {traceback.format_exc()}")
            return "Давайте поговорим о чем-нибудь интересном!"
    
    def build_knowledge_aware_prompt(self, user_message: str, relevant_knowledge: str) -> str:
        """Строит промпт с учетом знаний о личности"""
        
        # Базовая информация о личности
        persona = self.knowledge_base.get_persona_description()
        
        if not self.conversation_history:
            if relevant_knowledge:
                return f"""Информация обо мне: {persona}
Релевантные факты: {relevant_knowledge}
Человек: {user_message}
Я:"""
            else:
                return f"""Информация обо мне: {persona}
Человек: {user_message}
Я:"""
        
        # С историей диалога
        context_lines = []
        for i, msg in enumerate(self.conversation_history[-2:]):
            corrected_msg = self.correct_third_person(msg)
            prefix = "Человек: " if i % 2 == 0 else "Я: "
            context_lines.append(f"{prefix}{corrected_msg}")
        
        context_str = "\n".join(context_lines)
        
        if relevant_knowledge:
            return f"""Информация обо мне: {persona}
Релевантные факты: {relevant_knowledge}
{context_str}
Человек: {user_message}
Я:"""
        else:
            return f"""Информация обо мне: {persona}
{context_str}
Человек: {user_message}
Я:"""
    
    def extract_and_enhance_response(self, full_text: str, original_prompt: str, user_message: str) -> str:
        """Извлекает ответ и улучшает его с учетом знаний"""
        
        response = full_text.replace(original_prompt, "").strip()
        response = self.advanced_cleaning(response)
        response = self.correct_third_person(response)
        response = self.remove_narrative_phrases(response)
        response = self.trim_to_last_complete_sentence(response)
        
        # Улучшаем ответ на основе знаний
        response = self.enhance_with_knowledge(response, user_message)
        
        return response
    
    def enhance_with_knowledge(self, response: str, user_message: str) -> str:
        """Улучшает ответ, добавляя персонализированные детали"""
        
        message_lower = user_message.lower()
        response_lower = response.lower()
        
        # Если спрашивают о имени, но в ответе его нет - добавляем
        if any(phrase in message_lower for phrase in ['как тебя зовут', 'твое имя']):
            if name := self.knowledge_base.knowledge.get("personal_info", {}).get("name"):
                if name.lower() not in response_lower:
                    if len(response) < 50:
                        response = f"Меня зовут {name}. {response}"
        
        # Если спрашивают о друзьях
        for friend in self.knowledge_base.knowledge.get("friends", {}):
            if friend.lower() in message_lower and friend.lower() not in response_lower:
                response = response.replace("он", friend).replace("она", friend)
        
        return response
    
    def get_knowledgeable_fallback(self, user_message: str) -> str:
        """Умные fallback-ответы с использованием знаний"""
        
        message_lower = user_message.lower()
        
        # Используем знания для персонализированных ответов
        if 'как тебя зовут' in message_lower:
            if name := self.knowledge_base.knowledge.get("personal_info", {}).get("name"):
                return f"Меня зовут {name}! А тебя?"
            else:
                return "Я еще не представился! Можешь назвать меня как хочешь)"
        
        if 'твои интересы' in message_lower or 'чем увлекаешься' in message_lower:
            if interests := list(self.knowledge_base.knowledge.get("interests", []))[:3]:
                return f"Я увлекаюсь {', '.join(interests)}. А что нравится тебе?"
        
        if 'твои друзья' in message_lower or 'с кем общаешься' in message_lower:
            if friends := list(self.knowledge_base.knowledge.get("friends", {}).keys())[:2]:
                return f"Общаюсь с {', '.join(friends)}. Хорошие ребята!"
        
        if 'сколько тебе лет' in message_lower or 'твой возраст' in message_lower:
            if age := self.knowledge_base.knowledge.get("personal_info", {}).get("age"):
                return f"Мне {age} лет. А тебе?"
        
        # Стандартные fallback-ы
        fallbacks = [
            "Интересный вопрос! Давай обсудим это подробнее.",
            "Хорошо, что спросил. Мое мнение по этому поводу...",
            "Понимаю, о чем ты. У меня похожие мысли!",
            "Да, это важная тема. Хочешь узнать мое мнение?",
            "Спасибо за вопрос! Давай поговорим об этом.",
        ]
        
        import numpy as np
        return np.random.choice(fallbacks)
    
    def calculate_response_length(self, user_message: str) -> int:
        """Динамически определяет длину ответа"""
        message_length = len(user_message.split())
        
        if message_length <= 3:
            return 20
        elif message_length <= 10:
            return 30
        else:
            return 40
    
    def correct_third_person(self, text: str) -> str:
        """Исправляет фразы в третьем лице"""
        corrections = [
            (r'сказал я', ''),
            (r'ответил я', ''),
            (r'спросил я', ''),
            (r'добавил я', ''),
            (r',?\s*сказал\s+я[.!]?', ''),
        ]
        corrected = text
        for pattern, replacement in corrections:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        return corrected.strip()
    
    def remove_narrative_phrases(self, text: str) -> str:
        """Удаляет нарративные фразы"""
        narrative_patterns = [r'^[Яя]\s+(сказал|ответил)', r'потом\s+[Яя]']
        cleaned = text
        for pattern in narrative_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        return cleaned.strip()
    
    def advanced_cleaning(self, text: str) -> str:
        """Продвинутая очистка ответа"""
        patterns = [
            r'Assistant\s*:?\s*', r'User\s*:?\s*', r'Пользователь\s*:?\s*',
            r'Ассистент\s*:?\s*', r'Человек\s*:?\s*', r'<\|.*?\|>',
            r'Ты:\s*', r'Я:\s*', r'^[Ии]\s+',
        ]
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def trim_to_last_complete_sentence(self, text: str) -> str:
        """Обрезает до последнего полного предложения"""
        sentence_endings = r'[.!?…]'
        sentences = re.split(f'({sentence_endings})', text)
        if len(sentences) <= 1: return text
        complete_sentences = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                sentence = sentences[i] + sentences[i+1]
                if not self.contains_narrative_phrases(sentence):
                    complete_sentences.append(sentence)
        return ''.join(complete_sentences).strip() if complete_sentences else text
    
    def contains_narrative_phrases(self, text: str) -> bool:
        """Проверяет нарративные фразы"""
        narrative_indicators = [r'сказал я', r'ответил я', r'спросил я']
        for pattern in narrative_indicators:
            if re.search(pattern, text, re.IGNORECASE): return True
        return False
    
    def is_gibberish(self, text: str) -> bool:
        """Проверка на бессмысленный текст"""
        if len(text) < 3: return True
        if re.search(r'(.)\1{3,}', text): return True
        russian_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
        total_chars = max(len(re.findall(r'\w', text)), 1)
        return russian_chars / total_chars < 0.4

class CloneModel:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        
    def load_user_model(self, user_id: str) -> bool:
        """Загрузка модели для конкретного пользователя"""
        try:
            model_path = f"trained_models/user_{user_id}"
            
            if not os.path.exists(model_path):
                logger.warning(f"Модель для пользователя {user_id} не найдена")
                return False
            
            if user_id in self.models:
                logger.info(f"Модель для пользователя {user_id} уже загружена")
                return True
            
            logger.info(f"Загружаем модель для пользователя {user_id}")
            self.tokenizers[user_id] = AutoTokenizer.from_pretrained(model_path)
            self.models[user_id] = AutoModelForCausalLM.from_pretrained(model_path)
            
            if self.tokenizers[user_id].pad_token is None:
                self.tokenizers[user_id].pad_token = self.tokenizers[user_id].eos_token
            
            logger.info(f"✅ Модель для пользователя {user_id} успешно загружена")
            
            # ДОБАВЛЯЕМ: Создаем базу знаний при загрузке модели
            logger.info(f"🔄 Создаем базу знаний для пользователя {user_id}")
            from hybrid_knowledge_extractor import create_hybrid_knowledge_base
            knowledge = create_hybrid_knowledge_base(user_id)
            
            if knowledge.get("personal_info") or knowledge.get("interests"):
                logger.info(f"✅ База знаний создана: {len(knowledge.get('personal_info', {}))} фактов, {len(knowledge.get('interests', []))} интересов")
            else:
                logger.warning(f"⚠️ База знаний пустая или содержит мало информации")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели для {user_id}: {e}")
            return False
    
    def generate_response(self, user_id: str, message: str) -> str:
        """Генерация с использованием KnowledgeBase для принудительного применения знаний"""
        try:
            if user_id not in self.models:
                if not self.load_user_model(user_id):
                    return "Привет! Как дела?"
            
            # ВАЖНО: Используем KnowledgeBase для принудительного применения знаний
            knowledge_base = KnowledgeBase(user_id)
            
            # Сначала проверяем, есть ли прямой ответ в знаниях
            relevant_knowledge = knowledge_base.get_relevant_knowledge(message)
            if relevant_knowledge:
                logger.info(f"🎯 Найдены релевантные знания: {relevant_knowledge}")
                # Форматируем ответ на основе знаний
                return self.format_knowledge_answer(relevant_knowledge, message)
            
            # Если нет прямого ответа, используем генератор с учетом знаний
            from realtime_search_generator import RealtimeSearchGenerator
            generator = RealtimeSearchGenerator(self.models[user_id], self.tokenizers[user_id], user_id)
            response = generator.generate_response(message)
            
            return response
                
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            return "Давай поговорим о чем-нибудь интересном!"
    
    def format_knowledge_answer(self, knowledge: str, question: str) -> str:
        """Форматирует ответ на основе знаний"""
        question_lower = question.lower()
        
        # Если это вопрос об имени
        if any(phrase in question_lower for phrase in ['как тебя зовут', 'твое имя', 'представься']):
            if 'Меня зовут' in knowledge:
                return knowledge
            else:
                # Извлекаем имя из знаний
                name_match = re.search(r'Меня зовут (\w+)', knowledge)
                if name_match:
                    return f"Меня зовут {name_match.group(1)}"
                else:
                    # Пробуем извлечь любое имя
                    words = knowledge.split()
                    for word in words:
                        if word.istitle() and len(word) > 2 and word not in ['Меня', 'Мне', 'Мой']:
                            return f"Меня зовут {word}"
        
        # Если это вопрос о возрасте
        if any(phrase in question_lower for phrase in ['сколько лет', 'твой возраст']):
            if 'Мне' in knowledge and 'лет' in knowledge:
                return knowledge
        
        # Если это вопрос о городе
        if any(phrase in question_lower for phrase in ['откуда', 'город', 'живешь']):
            if 'Живу в' in knowledge:
                return knowledge
        
        # Возвращаем знания как есть
        return knowledge

class CloneShareService:
    def __init__(self):
        self.links_file = "clone_links.json"
        self.links = self.load_links()
    
    def load_links(self):
        """Загрузка ссылок из файла"""
        try:
            if os.path.exists(self.links_file):
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    links = json.load(f)
                    logger.info(f"✅ Загружено {len(links)} токенов из файла")
                    return links
            else:
                logger.info("Файл ссылок не найден, создаем новый")
                links = {}
                self.save_links(links)
                return links
        except Exception as e:
            logger.error(f"Ошибка загрузки ссылок: {e}")
            return {}
    
    def save_links(self, links=None):
        """Сохранение ссылок в файл"""
        try:
            if links is None:
                links = self.links
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
            logger.info("✅ Ссылки сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {e}")
    
    def generate_share_link(self, user_id: str, clone_name: str) -> str:
        """Генерация ссылки для доступа к клону"""
        try:
            logger.info(f"🔗 Генерация ссылки для user_id: {user_id}, clone_name: {clone_name}")
            
            # Сначала деактивируем старые ссылки для этого пользователя
            deactivated_count = 0
            for token, info in list(self.links.items()):
                if info.get('user_id') == user_id and info.get('active', True):
                    info['active'] = False
                    deactivated_count += 1
            
            if deactivated_count > 0:
                logger.info(f"🗑️ Деактивировано {deactivated_count} старых ссылок")
            
            # Создаем новую ссылку
            token = str(uuid.uuid4())
            
            self.links[token] = {
                'user_id': user_id,
                'name': clone_name,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            self.save_links()
            
            logger.info(f"✅ Сгенерирован токен для {user_id}: {token}")
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ссылки: {e}")
            return str(uuid.uuid4())
    
    def get_user_id_by_token(self, token: str):
        """Получение user_id по токену"""
        logger.info(f"🔍 Поиск user_id для токена: {token}")
        
        if token in self.links:
            link_info = self.links[token]
            is_active = link_info.get('active', True)
            user_id = link_info.get('user_id')
            
            logger.info(f"📋 Найден токен: active={is_active}, user_id={user_id}")
            
            if is_active:
                return user_id
            else:
                logger.warning(f"❌ Токен {token} неактивен")
        else:
            logger.warning(f"❌ Токен {token} не найден в базе")
        
        return None
    
    def get_all_links(self):
        """Получение всех активных ссылок"""
        active_links = {}
        for token, info in self.links.items():
            if info.get('active', True):
                active_links[token] = info
        
        logger.info(f"📊 Активных ссылок: {len(active_links)}")
        return active_links

    def get_user_links(self, user_id: str):
        """Получение всех ссылок пользователя"""
        user_links = {}
        for token, info in self.links.items():
            if info.get('user_id') == user_id:
                user_links[token] = info
        
        logger.info(f"👤 Пользователь {user_id} имеет {len(user_links)} ссылок")
        return user_links

# Инициализация сервисов
clone_model = CloneModel()
share_service = CloneShareService()

@app.get("/")
async def root():
    return {"message": "AI Clone Server is running!", "status": "active"}

@app.get("/status")
async def status():
    active_models = len(clone_model.models)
    active_links = len(share_service.get_all_links())
    return {
        "status": "running",
        "active_models": active_models,
        "active_links": active_links,
        "total_tokens": len(share_service.links)
    }

@app.get("/debug/links")
async def debug_links():
    """Отладочная информация о ссылках"""
    return {
        "all_links": share_service.links,
        "active_links": share_service.get_all_links()
    }

@app.get("/clone/{token}")
async def get_clone_info(token: str):
    """Информация о клоне"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    clone_info = share_service.links.get(token, {})
    return {
        "clone_name": clone_info.get('name', 'Unknown'),
        "user_id": user_id,
        "created_at": clone_info.get('created_at'),
        "status": "active"
    }

@app.post("/clone/{token}/chat")
async def chat_with_clone(token: str, request: ChatRequest):
    """Чат с AI-клоном"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    try:
        response = clone_model.generate_response(user_id, request.message)
        return ChatResponse(response=response)
    
    except Exception as e:
        logger.error(f"Ошибка в чате с клоном {token}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/user/{user_id}/refresh_knowledge")
async def refresh_knowledge(user_id: str):
    """Принудительное обновление знаний пользователя"""
    try:
        extractor = KnowledgeExtractor(user_id)
        success = extractor.extract_and_save_knowledge()
        
        if success:
            return {"status": "success", "message": "Knowledge refreshed"}
        else:
            return {"status": "error", "message": "Failed to refresh knowledge"}
            
    except Exception as e:
        logger.error(f"Ошибка обновления знаний: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/clone/{token}/web", response_class=HTMLResponse)
async def clone_web_interface(token: str):
    """Веб-интерфейс для чата с клоном"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        html_content = """
        <html>
            <head>
                <title>Клон не найден</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        max-width: 800px; 
                        margin: 0 auto; 
                        padding: 40px; 
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container {
                        background: white;
                        border-radius: 15px;
                        padding: 40px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    h1 { color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Клон не найден</h1>
                    <p>Ссылка недействительна или клон был удален.</p>
                    <p><small>Токен: """ + token + """</small></p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    clone_info = share_service.links.get(token, {})
    clone_name = clone_info.get('name', 'AI Клон')
    created_at = clone_info.get('created_at', 'Неизвестно')
    
    # Форматируем дату
    try:
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        formatted_date = created_dt.strftime("%d.%m.%Y %H:%M")
    except:
        formatted_date = created_at
    
    html_content = f"""
    <html>
        <head>
            <title>{clone_name} - AI Клон</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 20px;
                }}
                .chat-container {{ 
                    border: 2px solid #e0e0e0; 
                    padding: 20px; 
                    height: 400px; 
                    overflow-y: scroll; 
                    margin-bottom: 20px;
                    border-radius: 10px;
                    background: #fafafa;
                }}
                .message {{ 
                    margin: 15px 0; 
                    padding: 12px 16px; 
                    border-radius: 15px;
                    max-width: 80%;
                    word-wrap: break-word;
                }}
                .user {{ 
                    background: #007bff; 
                    color: white;
                    margin-left: auto;
                    margin-right: 0;
                }}
                .bot {{ 
                    background: #f1f3f4; 
                    color: #333;
                    margin-left: 0;
                    margin-right: auto;
                }}
                .input-group {{
                    display: flex;
                    gap: 10px;
                }}
                input {{ 
                    flex: 1; 
                    padding: 12px; 
                    border: 2px solid #ddd;
                    border-radius: 25px;
                    font-size: 16px;
                }}
                input:focus {{
                    outline: none;
                    border-color: #007bff;
                }}
                button {{ 
                    padding: 12px 25px; 
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    cursor: pointer;
                    border-radius: 25px;
                    font-size: 16px;
                    transition: background 0.3s;
                }}
                button:hover {{
                    background: #0056b3;
                }}
                .info {{
                    background: #e7f3ff;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    border-left: 4px solid #007bff;
                }}
                .token-info {{
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 12px;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 {clone_name}</h1>
                    <p>AI клон обучен на стиле общения пользователя</p>
                    <div class="info">
                        <strong>ℹ️ Информация:</strong><br>
                        • Создан: {formatted_date}<br>
                        • Модель: Russian GPT-2 с дообучением<br>
                        • Просто начните диалог ниже!
                        <div class="token-info">Токен: {token}</div>
                    </div>
                </div>
                
                <div id="chat" class="chat-container"></div>
                
                <div class="input-group">
                    <input type="text" id="message" placeholder="Введите ваше сообщение..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
            </div>
            
            <script>
                const chat = document.getElementById('chat');
                const messageInput = document.getElementById('message');
                
                function addMessage(text, isUser) {{
                    const messageDiv = document.createElement('div');
                    messageDiv.className = isUser ? 'message user' : 'message bot';
                    messageDiv.textContent = text;
                    chat.appendChild(messageDiv);
                    chat.scrollTop = chat.scrollHeight;
                }}
                
                function handleKeyPress(event) {{
                    if (event.key === 'Enter') {{
                        sendMessage();
                    }}
                }}
                
                async function sendMessage() {{
                    const message = messageInput.value.trim();
                    if (!message) return;
                    
                    addMessage(message, true);
                    messageInput.value = '';
                    messageInput.disabled = true;
                    
                    try {{
                        const response = await fetch('/clone/{token}/chat', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ message: message }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error('Ошибка сервера');
                        }}
                        
                        const data = await response.json();
                        addMessage(data.response, false);
                    }} catch (error) {{
                        addMessage('❌ Ошибка соединения с сервером', false);
                    }} finally {{
                        messageInput.disabled = false;
                        messageInput.focus();
                    }}
                }}
                
                // Приветственное сообщение
                addMessage('Привет! Я ваш AI-клон, обученный на вашем стиле общения. Давайте пообщаемся!', false);
                
                // Фокус на поле ввода
                messageInput.focus();
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/user/{user_id}/links")
async def get_user_links(user_id: str):
    """Получить все ссылки пользователя"""
    user_links = share_service.get_user_links(user_id)
    return {
        "user_id": user_id,
        "links": user_links,
        "total": len(user_links)
    }

@app.delete("/clone/{token}")
async def delete_clone_link(token: str):
    """Удалить ссылку на клона"""
    if token in share_service.links:
        share_service.links[token]['active'] = False
        share_service.save_links()
        return {"status": "deleted", "token": token}
    else:
        raise HTTPException(status_code=404, detail="Token not found")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Запускаем AI Clone Server...")
    logger.info("📊 Статус ссылок при запуске:")
    
    # Проверяем ссылки при запуске
    active_links = share_service.get_all_links()
    logger.info(f"✅ Активных ссылок: {len(active_links)}")
    
    for token, info in active_links.items():
        logger.info(f"   - {token}: {info.get('name')} (user: {info.get('user_id')})")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)