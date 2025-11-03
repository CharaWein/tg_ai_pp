# hybrid_knowledge_extractor.py
import os
import json
import logging
import re
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class HybridKnowledgeExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.raw_data_path = f"user_data/{user_id}/training_data.json"
        self.knowledge_path = f"user_data/{user_id}/knowledge_base.json"

    def extract_and_save_knowledge(self) -> bool:
        """Сохраняем расширенные знания с помощью шаблонов"""
        try:
            if not os.path.exists(self.raw_data_path):
                logger.warning(f"❌ Файл данных не найден: {self.raw_data_path}")
                return False
            
            with open(self.raw_data_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            # Берем ВСЕ сообщения
            all_messages = [msg.get('text', '') for msg in raw_data if msg.get('text')]
            
            if not all_messages:
                logger.warning("❌ Нет сообщений для извлечения знаний")
                return False
            
            logger.info(f"📊 Обрабатываем {len(all_messages)} сообщений для извлечения знаний")
            
            # Расширенные знания для промпта
            knowledge = {
                "personal_info": self.extract_personal_info(all_messages),
                "interests": self.extract_interests(" ".join(all_messages)),
                "habits": self.extract_habits(" ".join(all_messages)),
                "friends": self.extract_friends(all_messages),
                "work_education": self.extract_work_education(all_messages),
                "all_messages": all_messages[:200],  # Сохраняем сообщения для real-time поиска
                "extraction_date": datetime.now().isoformat(),
                "source_messages": len(all_messages),
                "extraction_method": "enhanced_pattern_matching"
            }
            
            # Сохраняем
            os.makedirs(os.path.dirname(self.knowledge_path), exist_ok=True)
            with open(self.knowledge_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge, f, ensure_ascii=False, indent=2)
            
            logger.info("✅ Расширенные знания сохранены для real-time поиска")
            logger.info(f"📝 Извлечено: {len(knowledge['personal_info'])} фактов, {len(knowledge['interests'])} интересов")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения знаний: {e}")
            return False

    def extract_personal_info(self, messages: List[str]) -> Dict[str, str]:
        """Извлечение персональной информации с помощью шаблонов"""
        info = {}
        all_text = " ".join(messages).lower()
        
        # Имя - различные паттерны
        name_patterns = [
            r'меня зовут\s+([А-Я][а-я]{2,})',
            r'мое имя\s+([А-Я][а-я]{2,})',
            r'я\s+([А-Я][а-я]{2,})',
            r'зовите меня\s+([А-Я][а-я]{2,})'
        ]
        
        for msg in messages:
            for pattern in name_patterns:
                match = re.search(pattern, msg, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    common_names = ['андрей', 'алексей', 'сергей', 'дмитрий', 'иван', 'максим', 'артем', 'владимир']
                    if any(common_name in name.lower() for common_name in common_names):
                        info["name"] = name
                        break
            if "name" in info:
                break
        
        # Возраст
        age_patterns = [
            r'мне\s+(\d{1,2})\s+лет',
            r'возраст\s+(\d{1,2})',
            r'(\d{1,2})\s+год'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, all_text)
            if match:
                info["age"] = match.group(1)
                break
        
        # Город
        city_patterns = [
            r'живу в\s+([А-Я][а-я]+)',
            r'город\s+([А-Я][а-я]+)',
            r'из\s+([А-Я][а-я]+)',
            r'в\s+([А-Я][а-я]+)\s+живу'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, all_text)
            if match:
                info["city"] = match.group(1)
                break
        
        # Работа
        work_patterns = [
            r'работаю\s+([^.,!?]+)',
            r'занимаюсь\s+([^.,!?]+)',
            r'профессия\s+([^.,!?]+)'
        ]
        
        for pattern in work_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                info["work"] = match.group(1).strip()
                break
        
        return info

    def extract_interests(self, all_text: str) -> List[str]:
        """Извлечение интересов по ключевым словам"""
        interests = []
        interest_keywords = {
            'программирование': ['python', 'программирование', 'код', 'разработка', 'алгоритм'],
            'игры': ['игр', 'гейм', 'steam', 'консоль', 'прохождение'],
            'музыка': ['музык', 'песн', 'альбом', 'концерт', 'гитар'],
            'спорт': ['спорт', 'футбол', 'хоккей', 'тренировк', 'бег'],
            'кино': ['фильм', 'кино', 'сериал', 'актер', 'режиссер'],
            'книги': ['книг', 'чтение', 'автор', 'роман', 'литератур'],
            'технологии': ['технологи', 'гаджет', 'смартфон', 'компьютер', 'ai'],
            'путешествия': ['путешеств', 'отпуск', 'отдых', 'страны', 'туризм'],
            'еда': ['еда', 'кулинар', 'рецепт', 'готовка', 'ресторан']
        }
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                interests.append(interest)
        
        return interests[:8]  # Ограничиваем количество

    def extract_habits(self, all_text: str) -> List[str]:
        """Извлечение привычек"""
        habits = []
        habit_indicators = {
            'утро': ['утром', 'просыпаюсь', 'завтрак'],
            'кофе': ['кофе', 'эспрессо', 'капучино'],
            'спорт': ['тренировка', 'зал', 'бегаю', 'йог'],
            'чтение': ['читаю', 'книга', 'статья'],
            'прогулки': ['гуляю', 'прогулка', 'парк']
        }
        
        for habit, indicators in habit_indicators.items():
            if any(indicator in all_text for indicator in indicators):
                habits.append(habit)
        
        return habits

    def extract_friends(self, messages: List[str]) -> Dict[str, str]:
        """Извлечение информации о друзьях"""
        friends = {}
        
        for msg in messages:
            # Поиск упоминаний имен друзей
            friend_matches = re.findall(r'(?:друг|подруг|знакомый)\s+([А-Я][а-я]{2,})', msg, re.IGNORECASE)
            for friend in friend_matches:
                if friend.lower() not in ['меня', 'тебя', 'себя']:  # Исключаем местоимения
                    friends[friend] = "друг"
        
        return friends

    def extract_work_education(self, messages: List[str]) -> Dict[str, str]:
        """Извлечение информации о работе и образовании"""
        work_edu = {}
        all_text = " ".join(messages).lower()
        
        # Работа
        work_patterns = {
            'работа': ['работаю', 'работа', 'профессия', 'должность'],
            'учеба': ['учусь', 'универ', 'институт', 'студент', 'курс']
        }
        
        for key, patterns in work_patterns.items():
            if any(pattern in all_text for pattern in patterns):
                work_edu[key] = "есть"
        
        return work_edu

# СТАРЫЙ КЛАСС - ОСТАВЛЯЕМ ДЛЯ СОВМЕСТИМОСТИ
class SmartKnowledgeExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.raw_data_path = f"user_data/{user_id}/training_data.json"
        self.knowledge_path = f"user_data/{user_id}/knowledge_base.json"
        
    def extract_and_save_knowledge(self) -> bool:
        """Совместимый метод для старого кода"""
        try:
            logger.info(f"🔄 Запускаем извлечение знаний для пользователя {self.user_id}")
            
            # Используем новый экстрактор
            extractor = HybridKnowledgeExtractor(self.user_id)
            success = extractor.extract_and_save_knowledge()
            
            if success:
                logger.info("✅ Знания успешно извлечены")
                return True
            else:
                logger.error("❌ Не удалось извлечь знания")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения знаний: {e}")
            return False

# НУЖНЫЕ ФУНКЦИИ ДЛЯ ИМПОРТА
def create_hybrid_knowledge_base(user_id: str) -> Dict[str, Any]:
    """Создает расширенную базу знаний с помощью шаблонов"""
    extractor = HybridKnowledgeExtractor(user_id)
    
    if extractor.extract_and_save_knowledge():
        knowledge_path = f"user_data/{user_id}/knowledge_base.json"
        if os.path.exists(knowledge_path):
            try:
                with open(knowledge_path, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    logger.info(f"✅ База знаний создана: {len(knowledge.get('personal_info', {}))} фактов, {len(knowledge.get('interests', []))} интересов")
                    return knowledge
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки базы знаний: {e}")
    
    # Fallback база знаний
    fallback_knowledge = {
        "personal_info": {},
        "interests": [],
        "habits": [],
        "friends": {},
        "work_education": {},
        "all_messages": [],
        "extraction_date": datetime.now().isoformat(),
        "extraction_method": "fallback_pattern_matching"
    }
    
    logger.warning("⚠️ Создана fallback база знаний")
    return fallback_knowledge

def extract_knowledge(user_id: str) -> bool:
    """Альтернативное название функции для совместимости"""
    return create_hybrid_knowledge_base(user_id) is not None

# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОЛНОЙ СОВМЕСТИМОСТИ
class KnowledgeExtractor:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.raw_data_path = f"user_data/{user_id}/training_data.json"
        self.knowledge_path = f"user_data/{user_id}/knowledge_base.json"
        
    def extract_and_save_knowledge(self) -> bool:
        """Совместимый метод для clone_server.py"""
        return create_hybrid_knowledge_base(self.user_id) is not None

# Экспортируем все нужные классы и функции
__all__ = [
    'HybridKnowledgeExtractor',
    'SmartKnowledgeExtractor', 
    'KnowledgeExtractor',
    'create_hybrid_knowledge_base',
    'extract_knowledge'
]