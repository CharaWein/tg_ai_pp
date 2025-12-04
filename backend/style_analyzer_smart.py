# style_analyzer_smart.py - Генератор промта в формате JSON

import os
import json
from datetime import datetime


class FormattedPromptGenerator:
    """Генерирует промт в JSON формате на основе структурированного системного промта"""

    def __init__(self, system_prompt_file="data/system_prompt.txt", facts_file="data/facts_advanced.json"):
        self.system_prompt_file = system_prompt_file
        self.facts_file = facts_file
        self.sections = self.load_system_prompt()
        self.facts = self.load_facts()

    def load_facts(self):
        """Загружает факты из JSON файла (если существует)"""
        try:
            with open(self.facts_file, "r", encoding="utf-8") as f:
                facts = json.load(f)
            print(f"✅ Факты загружены из {self.facts_file}")
            return facts
        except FileNotFoundError:
            print(f"⚠️ {self.facts_file} не найден, использую только системный промт")
            return {}
        except json.JSONDecodeError:
            print(f"⚠️ Ошибка чтения {self.facts_file}")
            return {}

    def load_system_prompt(self):
        """Загружает и парсит структурированный системный промт"""
        try:
            with open(self.system_prompt_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            print(f"✅ Системный промт загружен из {self.system_prompt_file}")
            
            # Парсинг основных секций
            sections = {}
            lines = content.split('\n')
            
            # Базовые секции
            sections['1_основная_личность'] = ""
            sections['2_образование'] = ""
            sections['3_хобби'] = ""
            sections['4_убеждения'] = ""
            sections['5_навыки'] = ""
            sections['6_стиль'] = ""
            sections['7_руководство'] = ""
            
            current_section = None
            
            for i, line in enumerate(lines):
                line = line.rstrip()
                
                # Определяем секции
                if '1. ОСНОВНАЯ ЛИЧНОСТЬ' in line:
                    current_section = '1_основная_личность'
                    continue
                elif '2. ОБРАЗОВАНИЕ И СПЕЦИАЛИЗАЦИЯ' in line:
                    current_section = '2_образование'
                    continue
                elif '3. ХОББИ И ИНТЕРЕСЫ' in line:
                    current_section = '3_хобби'
                    continue
                elif '4. УБЕЖДЕНИЯ И ЦЕННОСТИ' in line:
                    current_section = '4_убеждения'
                    continue
                elif '5. НАВЫКИ И ЭКСПЕРТИЗА' in line:
                    current_section = '5_навыки'
                    continue
                elif '6. СТИЛЬ ОБЩЕНИЯ' in line:
                    current_section = '6_стиль'
                    continue
                elif '7. РУКОВОДСТВО ДЛЯ ОТВЕТОВ' in line:
                    current_section = '7_руководство'
                    continue
                elif line.startswith('#') or line.startswith('---'):
                    current_section = None
                    continue
                
                # Собираем содержимое секций
                if current_section and line.strip():
                    sections[current_section] += line + '\n'
            
            # Очищаем лишние переносы
            for key in sections:
                sections[key] = sections[key].strip()
            
            print(f"📊 Извлечено секций: {len([v for v in sections.values() if v])}")
            return sections
            
        except FileNotFoundError:
            print(f"⚠️ {self.system_prompt_file} не найден!")
            return {}

    def create_system_prompt_text(self, sections, facts):
        """Создает текстовую часть system_prompt"""
        
        # Основная личность
        basic_info = []
        if facts.get("personal", {}).get("full_name"):
            basic_info.append(f"ТЫ - {facts['personal']['full_name'].upper()}")
        else:
            basic_info.append("ТЫ - UNKNOWN")
        
        basic_info.append("═══════════════════════════════════════════════════════════════\n")
        
        # Информация о личности
        personal_lines = []
        if sections.get('1_основная_личность'):
            personal_lines.append(sections['1_основная_личность'])
        
        # Образование
        if sections.get('2_образование'):
            personal_lines.append(sections['2_образование'])
        
        # Друзья (из facts если есть)
        friends = facts.get("social", {}).get("friends", [])
        if friends:
            friends_str = ", ".join(friends[:4])
            if len(friends) > 4:
                friends_str += f" и ещё {len(friends)-4} человек"
            personal_lines.append(f"\nТвои друзья: {friends_str}.")
            
            best_friend = facts.get("social", {}).get("best_friend")
            if best_friend:
                personal_lines.append(f"{best_friend} — твой лучший друг.")
        
        # Хобби и интересы
        hobbies_section = "\n\nИНТЕРЕСЫ И ХОББИ:"
        hobby_lines = []
        
        if facts.get("hobbies", {}).get("games"):
            games = facts["hobbies"]["games"][:5]
            hobby_lines.append(f"🎮 Любимые игры: {', '.join(games)}")
        
        if facts.get("hobbies", {}).get("music"):
            music = facts["hobbies"]["music"]
            if isinstance(music, list):
                hobby_lines.append(f"🎵 Музыка: {', '.join(music[:3])}")
            else:
                hobby_lines.append(f"🎵 Музыка: {music}")
        
        if facts.get("hobbies", {}).get("programming") or facts.get("hobbies", {}).get("strategy_games"):
            interests = []
            if facts["hobbies"].get("programming"):
                interests.append("программирование")
            if facts["hobbies"].get("strategy_games"):
                interests.append("стратегические игры")
            hobby_lines.append(f"⚡ Увлечения: {', '.join(interests)}")
        
        if sections.get('3_хобби'):
            hobby_lines.append(f"💫 Прочие интересы: {sections['3_хобби']}")
        
        # Убеждения
        beliefs_section = "\n\n✊ Убеждения:"
        belief_lines = []
        
        if facts.get("beliefs", {}).get("core_beliefs"):
            for belief in facts["beliefs"]["core_beliefs"][:3]:
                belief_lines.append(f"  {belief};")
        
        if facts.get("beliefs", {}).get("life_goal"):
            belief_lines.append(f"\n🎯 Жизненная цель: {facts['beliefs']['life_goal']}")
        
        # Собираем все вместе
        system_prompt = "\n".join(basic_info) + "\n\n"
        system_prompt += "\n".join(personal_lines)
        
        if hobby_lines:
            system_prompt += hobbies_section + "\n" + "\n".join(hobby_lines)
        
        if belief_lines:
            system_prompt += beliefs_section + "\n" + "\n".join(belief_lines)
        
        # Инструкции для ответов
        instructions = "═══════════════════════════════════════════════════════════════\n"
        instructions += "ИНСТРУКЦИИ ДЛЯ ОТВЕТОВ:\n"
        instructions += "═══════════════════════════════════════════════════════════════\n\n"
        
        if sections.get('7_руководство'):
            guidelines = sections['7_руководство'].split('\n')
            for line in guidelines:
                if line.strip():
                    instructions += f"• {line.strip()}\n"
        
        # Основные принципы
        principles = "\n═══════════════════════════════════════════════════════════════\n"
        principles += "ГЛАВНОЕ: Будь самим собой. Ответы должны звучать как от \n"
        principles += "реального человека - с твоей личностью, юмором, честностью.\n\n"
        principles += "Когда спрашивают о твоих интересах, друзьях или убеждениях - \n"
        principles += "делись мнением с энтузиазмом и честностью. Используй свой \n"
        principles += "реальный опыт и то, что для тебя важно.\n"
        principles += "═══════════════════════════════════════════════════════════════"
        
        system_prompt += "\n\n" + instructions + principles
        
        return system_prompt

    def extract_user_profile(self, facts):
        """Создает структуру user_profile из facts"""
        user_profile = {
            "personal": {
                "birth_city": facts.get("personal", {}).get("birth_city", ""),
                "birth_date": facts.get("personal", {}).get("birth_date", ""),
                "age": facts.get("personal", {}).get("age", ""),
                "full_name": facts.get("personal", {}).get("full_name", "Unknown")
            },
            "location": {
                "country": facts.get("location", {}).get("country", ""),
                "current_city": facts.get("location", {}).get("current_city", "Unknown")
            },
            "education": {
                "university": facts.get("education", {}).get("university", []),
                "work": facts.get("education", {}).get("work", [])
            },
            "social": {
                "enemies": facts.get("social", {}).get("enemies", []),
                "friends": facts.get("social", {}).get("friends", []),
                "best_friend": facts.get("social", {}).get("best_friend", "")
            },
            "hobbies": {
                "likes": facts.get("hobbies", {}).get("likes", []),
                "music": facts.get("hobbies", {}).get("music", ""),
                "strategy_games": facts.get("hobbies", {}).get("strategy_games", False),
                "programming": facts.get("hobbies", {}).get("programming", False),
                "games": facts.get("hobbies", {}).get("games", [])
            },
            "beliefs": {
                "core_beliefs": facts.get("beliefs", {}).get("core_beliefs", []),
                "religion": facts.get("beliefs", {}).get("religion", ""),
                "life_goal": facts.get("beliefs", {}).get("life_goal", "")
            }
        }
        
        return user_profile

    def generate_json_prompt(self):
        """Генерирует промт в JSON формате как в примере"""
        if not self.sections and not self.facts:
            print("❌ Нет данных для генерации промта!")
            return None
        
        # Создаем структуру как в примере
        json_prompt = {
            "system_prompt": self.create_system_prompt_text(self.sections, self.facts),
            "generated_at": datetime.now().isoformat(),
            "generator_version": "3.0_FORMATTED",
            "user_profile": self.extract_user_profile(self.facts)
        }
        
        return json_prompt

    def save_prompt(self, output_file="data/prompt_template.json"):
        """Сохраняет промт в JSON файл"""
        json_prompt = self.generate_json_prompt()
        if json_prompt:
            os.makedirs(os.path.dirname(output_file) or "data", exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(json_prompt, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 JSON промт сохранен в: {output_file}")
            print(f"📊 Размер system_prompt: {len(json_prompt['system_prompt'])} символов")
            print(f"📁 Структура user_profile: {len(json_prompt['user_profile'])} секций")
            return True
        return False

    def display_prompt(self):
        """Выводит информацию о промте в консоль"""
        json_prompt = self.generate_json_prompt()
        if json_prompt:
            print("\n" + "=" * 80)
            print("📋 СГЕНЕРИРОВАННЫЙ JSON ПРОМТ:")
            print("=" * 80)
            
            print(f"\n📝 system_prompt (первые 500 символов):")
            print("-" * 40)
            preview = json_prompt['system_prompt'][:500]
            if len(json_prompt['system_prompt']) > 500:
                preview += "..."
            print(preview)
            
            print(f"\n📊 Информация о пользователе:")
            print("-" * 40)
            profile = json_prompt['user_profile']
            print(f"👤 Имя: {profile['personal']['full_name']}")
            print(f"📍 Город: {profile['location']['current_city']}")
            print(f"🎮 Хобби: {len(profile['hobbies']['games'])} игр, {len(profile['hobbies']['likes'])} интересов")
            print(f"🤝 Друзей: {len(profile['social']['friends'])}")
            
            print(f"\n📅 Сгенерировано: {json_prompt['generated_at']}")
            print("=" * 80)
            
            return True
        return False


if __name__ == "__main__":
    print("🤖 Загружаю анализатор стиля...\n")
    print("📁 Работаю с папкой: data/\n")

    generator = FormattedPromptGenerator(
        system_prompt_file="data/system_prompt.txt",
        facts_file="data/facts_advanced.json"
    )

    # Выводим информацию в консоль
    print("\n📋 АНАЛИЗИРУЮ ДАННЫЕ:\n")
    generator.display_prompt()

    # Сохраняем в файл
    generator.save_prompt("data/prompt_template.json")

    print("\n✅ Готово!")
    print("📁 prompt_template.json создан в папке data/")
    print("💡 Формат соответствует примеру с system_prompt и user_profile")