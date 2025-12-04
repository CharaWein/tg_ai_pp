# 0_build_vector_db_improved.py - ИНДЕКСИРОВАНИЕ + LLM-ПАРСИНГ ФАКТОВ (Mistral)

import json
import logging
import re
from pathlib import Path
from typing import List, Any, Dict
import chromadb
from chromadb.utils import embedding_functions
import requests
from config import MESSAGES_FILE, CHROMA_DB_DIR, DEBUG, OLLAMA_API_URL, OLLAMA_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama config - используем значения из config.py
OLLAMA_TIMEOUT = 600  # Увеличено до 10 минут для больших промптов
OLLAMA_MAX_RETRIES = 3  # Количество попыток при ошибках


class OllamaFactExtractor:
    """Использует Mistral 7B для извлечения фактов из сообщений"""

    @staticmethod
    def call_mistral(prompt: str, temperature: float = 0.3) -> str:
        """Вызывает Mistral 7B локально через Ollama с retry логикой"""
        import time
        
        for attempt in range(OLLAMA_MAX_RETRIES):
            try:
                logger.debug(f"🔄 Попытка {attempt + 1}/{OLLAMA_MAX_RETRIES} вызова Mistral...")
                
                # Ограничиваем размер промпта для избежания таймаутов
                max_prompt_length = 2000  # Ограничение длины промпта
                current_prompt = prompt
                if len(current_prompt) > max_prompt_length:
                    logger.warning(f"⚠️ Промпт слишком длинный ({len(current_prompt)} символов), обрезаю до {max_prompt_length}")
                    current_prompt = current_prompt[:max_prompt_length] + "..."
                
                response = requests.post(
                    f"{OLLAMA_API_URL}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": current_prompt,
                        "stream": False,
                        "temperature": temperature,
                    },
                    timeout=OLLAMA_TIMEOUT,
                )
                response.raise_for_status()
                result = response.json()
                
                if "response" not in result:
                    raise ValueError(f"Неожиданный ответ от Ollama: {result}")
                
                return result["response"]
                
            except requests.exceptions.Timeout:
                wait_time = (attempt + 1) * 5  # Экспоненциальная задержка
                logger.warning(f"⏱️ Таймаут при вызове Mistral (попытка {attempt + 1}/{OLLAMA_MAX_RETRIES}). Жду {wait_time} сек...")
                if attempt < OLLAMA_MAX_RETRIES - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("❌ Превышен таймаут после всех попыток")
                    raise
                    
            except requests.exceptions.ConnectionError:
                logger.error("❌ Ollama не запущена! Запусти: ollama serve")
                raise
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 500:
                    wait_time = (attempt + 1) * 3
                    logger.warning(f"⚠️ Ошибка 500 от Ollama (попытка {attempt + 1}/{OLLAMA_MAX_RETRIES}). Жду {wait_time} сек...")
                    if attempt < OLLAMA_MAX_RETRIES - 1:
                        time.sleep(wait_time)
                        continue
                raise
                
            except Exception as e:
                logger.error(f"❌ Ошибка при вызове Mistral: {e}")
                if attempt < OLLAMA_MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"🔄 Повторная попытка через {wait_time} сек...")
                    time.sleep(wait_time)
                    continue
                raise
        
        raise RuntimeError("Не удалось выполнить запрос после всех попыток")

    @staticmethod
    def extract_facts(messages: List[str]) -> Dict[str, Any]:
        """
        Использует Mistral для анализа сообщений и извлечения фактов
        """
        logger.info("🤖 Инициализирую Mistral 7B для анализа...")

        # Объединяем сообщения, отфильтровав явный мусор
        meaningful_messages = [
            str(msg) for msg in messages
            if msg and len(str(msg).strip()) > 3
            and not re.match(r'^(найти|http|^\d+:\d+)', str(msg).lower())
        ][:100]  # Берем первые 200 значимых сообщений

        messages_text = "\n".join(meaningful_messages)
        if not messages_text.strip():
            messages_text = "[Нет значимых сообщений]"

        logger.info(f"📝 Анализирую {len(meaningful_messages)} значимых сообщений...")

        # ===== STEP 1: ИЗВЛЕЧЕНИЕ ЛИЧНОЙ ИНФОРМАЦИИ =====
        logger.info("🔍 Step 1: Извлекаю личную информацию...")
        personal_prompt = f"""Проанализируй эти сообщения и извлеки личную информацию:

{messages_text[:300]}

Верни JSON (только JSON, без текста):
{{
    "full_name": "имя или null",
    "age": "возраст или null",
    "location": "город/страна или null",
    "timezone": "часовой пояс или null",
    "occupation": "профессия или null"
}}"""

        personal_response = OllamaFactExtractor.call_mistral(personal_prompt)
        try:
            personal_data = json.loads(personal_response)
        except json.JSONDecodeError:
            personal_data = {
                "full_name": None,
                "age": None,
                "location": None,
                "timezone": None,
                "occupation": None,
            }

        # ===== STEP 2: ИНТЕРЕСЫ И ХОББИ =====
        logger.info("🎮 Step 2: Извлекаю интересы и хобби...")
        hobbies_prompt = f"""Проанализируй эти сообщения и найди интересы:

{messages_text[:300]}

Верни JSON (только JSON):
{{
    "games": ["список игр если упоминаются"],
    "music": ["жанры музыки или артисты"],
    "programming": true/false если есть интерес к программированию,
    "sports": ["виды спорта"],
    "other_interests": ["другие интересы"]
}}"""

        hobbies_response = OllamaFactExtractor.call_mistral(hobbies_prompt)
        try:
            hobbies_data = json.loads(hobbies_response)
        except json.JSONDecodeError:
            hobbies_data = {
                "games": [],
                "music": [],
                "programming": False,
                "sports": [],
                "other_interests": [],
            }

        # ===== STEP 3: УБЕЖДЕНИЯ И ЦЕННОСТИ =====
        logger.info("🎯 Step 3: Извлекаю убеждения и ценности...")
        beliefs_prompt = f"""Проанализируй эти сообщения и определи убеждения человека:

{messages_text[:300]}

Верни JSON (только JSON):
{{
    "core_values": ["основные ценности человека"],
    "life_philosophy": "общая философия или null",
    "important_beliefs": ["важные убеждения"]
}}"""

        beliefs_response = OllamaFactExtractor.call_mistral(beliefs_prompt)
        try:
            beliefs_data = json.loads(beliefs_response)
        except json.JSONDecodeError:
            beliefs_data = {
                "core_values": [],
                "life_philosophy": None,
                "important_beliefs": [],
            }

        # ===== STEP 4: СТИЛЬ ОБЩЕНИЯ =====
        logger.info("💬 Step 4: Анализирую стиль общения...")
        style_prompt = f"""Проанализируй стиль общения в этих сообщениях:

{messages_text[:800]}

Верни JSON (только JSON):
{{
    "tone": "формальный/неформальный/смешанный",
    "personality_traits": ["черты характера"],
    "communication_style": "описание стиля",
    "keyword_style": ["частые слова/фразы"]
}}"""

        style_response = OllamaFactExtractor.call_mistral(style_prompt)
        try:
            style_data = json.loads(style_response)
        except json.JSONDecodeError:
            style_data = {
                "tone": "unknown",
                "personality_traits": [],
                "communication_style": "unknown",
                "keyword_style": [],
            }

        # ===== STEP 5: ОБРАЗОВАНИЕ И НАВЫКИ =====
        logger.info("💻 Step 5: Извлекаю образование и навыки...")
        skills_prompt = f"""Проанализируй эти сообщения и определи навыки:

{messages_text[:300]}

Верни JSON (только JSON):
{{
    "languages": ["языки программирования если упоминаются"],
    "skills": ["навыки и умения"],
    "education_level": "уровень образования или null",
    "specialization": "область специализации или null"
}}"""

        skills_response = OllamaFactExtractor.call_mistral(skills_prompt)
        try:
            skills_data = json.loads(skills_response)
        except json.JSONDecodeError:
            skills_data = {
                "languages": [],
                "skills": [],
                "education_level": None,
                "specialization": None,
            }

        # ===== СБОРКА ИТОГОВОГО JSON =====
        facts = {
            "personal": {
                "full_name": personal_data.get("full_name"),
                "age": personal_data.get("age"),
                "location": personal_data.get("location"),
                "timezone": personal_data.get("timezone"),
                "occupation": personal_data.get("occupation"),
            },
            "location": {
                "current_city": personal_data.get("location"),
            },
            "education": {
                "education_level": skills_data.get("education_level"),
                "specialization": skills_data.get("specialization"),
            },
            "hobbies": {
                "games": hobbies_data.get("games", []),
                "music": hobbies_data.get("music", []),
                "programming": hobbies_data.get("programming", False),
                "sports": hobbies_data.get("sports", []),
                "likes": hobbies_data.get("other_interests", []),
            },
            "skills": {
                "languages": skills_data.get("languages", []),
                "skills": skills_data.get("skills", []),
            },
            "beliefs": {
                "core_values": beliefs_data.get("core_values", []),
                "life_philosophy": beliefs_data.get("life_philosophy"),
                "core_beliefs": beliefs_data.get("important_beliefs", []),
            },
            "communication": {
                "tone": style_data.get("tone", "unknown"),
                "personality_traits": style_data.get("personality_traits", []),
                "style": style_data.get("communication_style", "unknown"),
                "keyword_style": style_data.get("keyword_style", []),
            },
            "raw_messages": meaningful_messages[:50],
            "extraction_method": "Mistral 7B (Ollama)",
        }

        # ===== ЛОГИРОВАНИЕ =====
        logger.info("\n✅ ИЗВЛЕЧЕНО:")
        logger.info(f"  👤 Имя: {facts['personal']['full_name']}")
        logger.info(f"  📍 Локация: {facts['personal']['location']}")
        logger.info(f"  🎮 Игр: {len(facts['hobbies']['games'])}")
        logger.info(f"  🎵 Музыки: {len(facts['hobbies']['music'])}")
        logger.info(f"  💻 Навыков: {len(facts['skills']['skills'])}")
        logger.info(f"  📊 Языков программирования: {len(facts['skills']['languages'])}")
        logger.info(f"  ✊ Ценностей: {len(facts['beliefs']['core_values'])}")
        logger.info(f"  💬 Черт характера: {len(facts['communication']['personality_traits'])}")

        return facts


class MessageProcessor:
    """Класс для обработки и очистки сообщений"""

    @staticmethod
    def clean_text(text: str) -> str:
        """Очистка текста от мусора"""
        if not isinstance(text, str):
            text = str(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def is_valid_message(message: Any) -> bool:
        """Проверка, что сообщение не мусорное"""
        if message is None:
            return False
        text = str(message).strip()
        if len(text) < 3:
            return False

        garbage_patterns = [
            r"^\s*$",
            r"^null$",
            r"^undefined$",
            r"^\[DELETED\]$",
            r"^\.\.\.$",
            r"^\[.*\]$",
            r"^[0-9:.\-\s]+$",
            r"^(ok|ок|да|нет|yes|no|пжлст|плз)$",
        ]

        for pattern in garbage_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return False
        return True

    @staticmethod
    def extract_metadata(message: Any) -> Dict[str, Any]:
        """Извлечение метаданных из сообщения"""
        if isinstance(message, dict):
            cleaned_msg = message.copy()
            for key, value in cleaned_msg.items():
                if isinstance(value, str):
                    cleaned_msg[key] = MessageProcessor.clean_text(value)
            return cleaned_msg
        else:
            cleaned_text = MessageProcessor.clean_text(message)
            return {
                "text": cleaned_text,
                "type": "text",
                "cleaned": True,
            }

    @staticmethod
    def prepare_messages(messages: List[Any]) -> tuple:
        """Обработка и подготовка всех сообщений"""
        valid_messages = []
        valid_texts = []
        valid_metadatas = []
        stats = {
            "total": len(messages),
            "valid": 0,
            "invalid": 0,
            "invalid_reasons": {},
        }

        for i, msg in enumerate(messages):
            if not MessageProcessor.is_valid_message(msg):
                stats["invalid"] += 1
                reason = "too_short" if len(str(msg).strip()) < 3 else "garbage_pattern"
                stats["invalid_reasons"][reason] = (
                    stats["invalid_reasons"].get(reason, 0) + 1
                )
                continue

            cleaned_message = MessageProcessor.extract_metadata(msg)

            if isinstance(cleaned_message, dict) and "text" in cleaned_message:
                text_for_vector = cleaned_message["text"]
            elif isinstance(cleaned_message, dict):
                text_for_vector = json.dumps(cleaned_message, ensure_ascii=False)
            else:
                text_for_vector = str(cleaned_message)

            vector_metadata = {
                "original_index": i,
                "message_length": len(text_for_vector),
                "processed": True,
            }

            valid_messages.append(cleaned_message)
            valid_texts.append(text_for_vector)
            valid_metadatas.append(vector_metadata)
            stats["valid"] += 1

        return valid_messages, valid_texts, valid_metadatas, stats


def build_vector_db():
    """Создает и индексирует ChromaDB базу с LLM-парсингом фактов"""
    logger.info("🔍 Анализирую messages...")

    if not Path(MESSAGES_FILE).exists():
        logger.error(f"❌ {MESSAGES_FILE} не найден!")
        logger.info("💡 Совет: Убедись что ты скопировал user_messages.json в data/")
        return False

    try:
        # Загружаем сообщения
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            messages = json.load(f)

        if isinstance(messages, dict):
            messages = [msg for msgs in messages.values() for msg in msgs]

        if not messages:
            logger.warning("⚠️ Сообщений не найдено в файле")
            return False

        logger.info(f"📝 Найдено {len(messages)} сырых сообщений")

        # Обрабатываем и очищаем сообщения
        processor = MessageProcessor()
        cleaned_messages, texts, metadatas, stats = processor.prepare_messages(
            messages
        )

        logger.info(f"📊 СТАТИСТИКА ОЧИСТКИ:")
        logger.info(f" ✅ Валидных сообщений: {stats['valid']}")
        logger.info(f" 🗑️ Отфильтровано: {stats['invalid']}")
        if stats["invalid_reasons"]:
            for reason, count in stats["invalid_reasons"].items():
                logger.info(f" • {reason}: {count}")

        # ===== ИЗВЛЕЧЕНИЕ ФАКТОВ С MISTRAL =====
        logger.info("\n📌 ИЗВЛЕКАЮ ФАКТЫ С ПОМОЩЬЮ MISTRAL 7B...")
        extractor = OllamaFactExtractor()
        facts = extractor.extract_facts(texts if texts else messages)

        # Сохраняем факты
        facts_path = Path(MESSAGES_FILE).parent / "facts_advanced.json"
        with open(facts_path, "w", encoding="utf-8") as f:
            json.dump(facts, f, ensure_ascii=False, indent=2)
        logger.info(f"\n💾 Факты сохранены в: {facts_path}")

        # Сохраняем очищенные сообщения
        cleaned_messages_path = Path(MESSAGES_FILE).parent / "cleaned_messages.json"
        with open(cleaned_messages_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_messages, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Очищенные сообщения сохранены в: {cleaned_messages_path}")

        # Создаем ChromaDB
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

        try:
            client.delete_collection(name="user_messages")
            logger.info("🗑️ Удалена старая коллекция")
        except Exception as e:
            logger.debug(f"ℹ️ Коллекция не существовала: {e}")

        embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="paraphrase-multilingual-MiniLM-L12-v2"
            )
        )

        collection = client.create_collection(
            name="user_messages", embedding_function=embedding_function
        )

        if texts:
            logger.info(f"📊 Индексирую {len(texts)} очищенных документов...")

            BATCH_SIZE = 1000
            ids = [f"msg_{i}" for i in range(len(texts))]
            total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(
                f"🔄 Обрабатываю {total_batches} батчей по {BATCH_SIZE} сообщений..."
            )

            for batch_num in range(total_batches):
                start_idx = batch_num * BATCH_SIZE
                end_idx = min((batch_num + 1) * BATCH_SIZE, len(texts))
                batch_ids = ids[start_idx:end_idx]
                batch_texts = texts[start_idx:end_idx]
                batch_metadatas = metadatas[start_idx:end_idx]

                collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas,
                )

                if (batch_num + 1) % 10 == 0 or (batch_num + 1) == total_batches:
                    logger.info(
                        f"✅ Батч {batch_num + 1}/{total_batches} обработан ({end_idx - start_idx} сообщений)"
                    )

        logger.info(f"\n✅ ChromaDB collection создана!")
        logger.info(f" 📁 Путь: {CHROMA_DB_DIR}")
        logger.info(f" 📊 Документов: {len(texts)}")
        logger.info(f" 💾 JSON факты: {facts_path}")
        logger.info(f" 💾 JSON сообщения: {cleaned_messages_path}")
        if stats["total"] > 0:
            logger.info(
                f" 🎯 Эффективность: {stats['valid']}/{stats['total']} ({stats['valid']/stats['total']*100:.1f}%)"
            )

        # Проверяем что база работает
        try:
            if texts:
                test_count = collection.count()
                logger.info(f" ✅ Проверка: в коллекции {test_count} документов")

                results = collection.query(query_texts=["тест"], n_results=2)
                logger.info(
                    f" 🔎 Тестовый поиск: найдено {len(results['documents'][0])} результатов"
                )
            else:
                logger.info(f" ℹ️ Коллекция пуста (нет валидных сообщений)")
        except Exception as e:
            logger.warning(f" ⚠️ Не удалось проверить коллекцию: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при индексировании: {e}")
        if DEBUG:
            import traceback

            logger.error(f"🔍 Детали ошибки: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = build_vector_db()
    exit(0 if success else 1)
