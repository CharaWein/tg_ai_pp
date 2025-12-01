# style_analyzer_smart.py - Генератор промта с фактами из Mistral

import json
import os
from datetime import datetime


class FormattedPromptGenerator:
    """Генерирует промт с четкой структурой на основе фактов от Mistral"""

    def __init__(self, facts_file="data/facts_advanced.json"):
        self.facts_file = facts_file
        self.user_facts = self.load_facts()

    def load_facts(self):
        """Загружает факты из JSON файла (созданного Mistral)"""
        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                facts = json.load(f)
            print(f"✅ Факты загружены из {self.facts_file}")
            print(f"   📊 Метод: {facts.get('extraction_method', 'unknown')}")
            return facts
        except FileNotFoundError:
            print(f"⚠️ {self.facts_file} не найден!")
            print("💡 Запусти сначала: python build_vector_db_mistral.py")
            return {}

    def generate_full_prompt(self):
        """Генерирует ПОЛНЫЙ многоуровневый промт с фактами"""
        facts = self.user_facts

        if not facts:
            print("❌ Факты не загружены!")
            return None

        # ============================================================
        # 1. ОСНОВНАЯ ЛИЧНОСТЬ
        # ============================================================
        personal = facts.get("personal", {})
        location = facts.get("location", {})

        full_name = personal.get("full_name") or "Unknown"
        current_city = location.get("current_city") or "Unknown"
        age = personal.get("age")
        occupation = personal.get("occupation")

        section1 = f"Ты {full_name}. Живешь в {current_city}."
        if age:
            section1 += f" Тебе {age} лет."
        if occupation:
            section1 += f" Работаешь как {occupation}."

        print(f"✅ Part 1 (Личность): {full_name}, {current_city}")

        # ============================================================
        # 2. ОБРАЗОВАНИЕ И СПЕЦИАЛИЗАЦИЯ
        # ============================================================
        education = facts.get("education", {})
        education_level = education.get("education_level")
        specialization = education.get("specialization")

        section2 = ""
        if education_level:
            section2 = f"Уровень образования: {education_level}."
        if specialization:
            if section2:
                section2 += f" Специализация: {specialization}."
            else:
                section2 = f"Специализация: {specialization}."

        print(f"✅ Part 2 (Образование): {education_level or 'N/A'}")

        # ============================================================
        # 3. ХОББИ И ИНТЕРЕСЫ
        # ============================================================
        hobbies = facts.get("hobbies", {})

        section3_items = []

        # Игры
        games = hobbies.get("games", [])
        if games:
            games_str = ", ".join(games[:5])
            section3_items.append(f"🎮 Любимые игры: {games_str}")
            print(f"✅ Игры: {games_str}")

        # Музыка
        music = hobbies.get("music", [])
        if music:
            if isinstance(music, list):
                music_str = ", ".join(music[:3])
            else:
                music_str = str(music)
            section3_items.append(f"🎵 Музыка: {music_str}")
            print(f"✅ Музыка: {music_str}")

        # Программирование
        if hobbies.get("programming"):
            section3_items.append("💻 Интересуешься программированием")
            print(f"✅ Программирование: да")

        # Спорт
        sports = hobbies.get("sports", [])
        if sports:
            sports_str = ", ".join(sports[:3])
            section3_items.append(f"⚽ Спорт: {sports_str}")
            print(f"✅ Спорт: {sports_str}")

        # Другие интересы
        likes = hobbies.get("likes", [])
        if likes:
            unique_likes = list(set(likes))[:6]
            likes_str = ", ".join(unique_likes)
            section3_items.append(f"💫 Интересы: {likes_str}")
            print(f"✅ Интересы: {len(unique_likes)} уникальных")

        section3 = "\n".join(section3_items)

        # ============================================================
        # 4. УБЕЖДЕНИЯ И ЦЕННОСТИ
        # ============================================================
        beliefs = facts.get("beliefs", {})
        section4_items = []

        # Ценности
        core_values = beliefs.get("core_values", [])
        if core_values:
            values_str = ", ".join(core_values[:3])
            section4_items.append(f"✊ Ценности: {values_str}")
            print(f"✅ Ценности: {values_str}")

        # Философия жизни
        life_philosophy = beliefs.get("life_philosophy")
        if life_philosophy:
            section4_items.append(f"🎯 Философия: {life_philosophy}")
            print(f"✅ Философия жизни: {life_philosophy}")

        # Убеждения
        core_beliefs = beliefs.get("core_beliefs", [])
        if core_beliefs:
            beliefs_str = ";\n ".join(core_beliefs[:3])
            section4_items.append(f"📖 Убеждения:\n {beliefs_str}.")
            print(f"✅ Убеждений: {len(core_beliefs)}")

        section4 = "\n".join(section4_items)

        # ============================================================
        # 5. НАВЫКИ И ЭКСПЕРТИЗА
        # ============================================================
        skills = facts.get("skills", {})
        section5_items = []

        languages = skills.get("languages", [])
        if languages:
            lang_str = ", ".join(languages[:5])
            section5_items.append(f"💻 Языки программирования: {lang_str}")
            print(f"✅ Языки: {lang_str}")

        all_skills = skills.get("skills", [])
        if all_skills:
            skills_str = ", ".join(all_skills[:5])
            section5_items.append(f"🎯 Основные навыки: {skills_str}")
            print(f"✅ Навыков: {len(all_skills)}")

        section5 = "\n".join(section5_items)

        # ============================================================
        # 6. СТИЛЬ ОБЩЕНИЯ
        # ============================================================
        communication = facts.get("communication", {})

        section6_items = []

        tone = communication.get("tone")
        if tone and tone != "unknown":
            section6_items.append(f"🗣️ Тон: {tone}")

        personality = communication.get("personality_traits", [])
        if personality:
            pers_str = ", ".join(personality[:3])
            section6_items.append(f"💬 Характер: {pers_str}")

        style = communication.get("style")
        if style and style != "unknown":
            section6_items.append(f"📝 Стиль общения: {style}")

        section6 = "\n".join(section6_items)

        # ============================================================
        # 7. ИНСТРУКЦИИ ДЛЯ ОТВЕТОВ
        # ============================================================
        guidelines = [
            "Отвечай НАТУРАЛЬНО и ЧЕСТНО - как настоящий человек",
            "КРАТКОСТЬ: 1-3 предложения для простых вопросов, макс 5-7 для сложных",
            "РЕЛЕВАНТНОСТЬ: используй факты только если они по теме",
            "БЕЗ ПОВТОРОВ: не пересказывай одно и то же",
            "КОНТЕКСТ: помни предыдущие сообщения",
            "ЛИЧНОСТЬ: креативность, юмор, прямота",
            "БЕЗ ЛЕСТИ: дай честное мнение, даже если критичное",
            "ПРОАКТИВНОСТЬ: иногда задавай встречные вопросы",
            "ИЗБЕГАЙ: клише типа 'рад помочь', повторяющихся приветствий",
            "СПЕЦИФИКА: Ссылайся на свои интересы и убеждения",
            "ЮМОР: добавляй легкий сарказм если уместно",
            "ЧЕСТНОСТЬ: не выдумывай, если не знаешь",
        ]

        guidelines_text = "\n".join([f"• {g}" for g in guidelines])

        # ============================================================
        # СБОРКА ПОЛНОГО ПРОМТА
        # ============================================================
        full_prompt = f"""# СИСТЕМА ПЕРСОНАЖА

## 1. ОСНОВНАЯ ЛИЧНОСТЬ
{section1}

## 2. ОБРАЗОВАНИЕ И СПЕЦИАЛИЗАЦИЯ
{section2 if section2 else 'Информация не указана'}

## 3. ХОББИ И ИНТЕРЕСЫ
{section3 if section3_items else 'Информация не указана'}

## 4. УБЕЖДЕНИЯ И ЦЕННОСТИ
{section4 if section4_items else 'Информация не указана'}

## 5. НАВЫКИ И ЭКСПЕРТИЗА
{section5 if section5_items else 'Информация не указана'}

## 6. СТИЛЬ ОБЩЕНИЯ
{section6 if section6_items else 'Информация не указана'}

## 7. РУКОВОДСТВО ДЛЯ ОТВЕТОВ

{guidelines_text}

---

## ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ

**Метод извлечения фактов:** {facts.get('extraction_method', 'Unknown')}

**Анализировано сообщений:** {len(facts.get('raw_messages', []))}

**Генерировано:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## ПРИМЕРЫ СООБЩЕНИЙ (из истории)

{chr(10).join([f'> {msg[:100]}...' if len(str(msg)) > 100 else f'> {msg}' for msg in facts.get('raw_messages', [])[:10]])}
"""

        return full_prompt

    def save_prompt(self, output_file="data/system_prompt.txt"):
        """Сохраняет промт в файл"""
        prompt = self.generate_full_prompt()
        if prompt:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(prompt)
            print(f"\n💾 Промт сохранен в: {output_file}")
            print(f"📊 Размер: {len(prompt)} символов")
            return True
        return False

    def display_prompt(self):
        """Выводит промт в консоль"""
        prompt = self.generate_full_prompt()
        if prompt:
            print("\n" + "=" * 80)
            print(prompt)
            print("=" * 80)
            return True
        return False


if __name__ == "__main__":
    print("🤖 Загружаю анализатор стиля (Mistral-enhanced)...\n")

    generator = FormattedPromptGenerator()

    # Выводим в консоль
    print("\n📋 ГЕНЕРИРУЮ ПОЛНЫЙ ПРОМТ:\n")
    generator.display_prompt()

    # Сохраняем в файл
    generator.save_prompt()

    print("\n✅ Готово!")
    print("💡 Использование: импортируй FormattedPromptGenerator в свой бот")
