import asyncio
import json
import os
import re
from telethon import TelegramClient
from telethon.tl.types import PeerUser, PeerChat, PeerChannel, User, Channel
from telethon.utils import get_display_name
from dotenv import load_dotenv

load_dotenv()

class QuestionGenerator:
    """Генератор контекстных вопросов для ответов"""
    
    @staticmethod
    def generate_question_for_answer(text):
        """Генерирует подходящий вопрос для данного ответа"""
        text_lower = text.lower().strip()
        
        # Определяем тип сообщения и генерируем соответствующий вопрос
        if any(word in text_lower for word in ['привет', 'здаров', 'хай', 'hello', 'hi']):
            return "Как поздороваться с другом?"
        
        elif any(word in text_lower for word in ['пока', 'до свидания', 'увидимся', 'bye']):
            return "Как попрощаться?"
        
        elif any(word in text_lower for word in ['спасибо', 'благодарю', 'thanks']):
            return "Как поблагодарить человека?"
        
        elif any(word in text_lower for word in ['как дела', 'как ты', 'че как']):
            return "Как спросить как дела?"
        
        elif any(word in text_lower for word in ['норм', 'хорошо', 'отлично', 'нормально']):
            return "Как ответить на вопрос 'как дела'?"
        
        elif any(word in text_lower for word in ['плохо', 'устал', 'устала', 'уставш']):
            return "Как пожаловаться на усталость?"
        
        elif any(word in text_lower for word in ['что делаешь', 'чем занят']):
            return "Как спросить что человек делает?"
        
        elif any(word in text_lower for word in ['работаю', 'сижу', 'смотрю', 'играю']):
            return "Как рассказать о своих текущих занятиях?"
        
        elif any(word in text_lower for word in ['хочу', 'мечтаю', 'хотел бы']):
            return "Как поделиться своими желаниями?"
        
        elif any(word in text_lower for word in ['люблю', 'нравится', 'обожаю']):
            return "Как рассказать о своих предпочтениях?"
        
        elif any(word in text_lower for word in ['ненавижу', 'не люблю', 'раздражает']):
            return "Как выразить недовольство?"
        
        elif any(word in text_lower for word in ['сегодня', 'вчера', 'завтра']):
            if any(word in text_lower for word in ['кино', 'фильм', 'сериал']):
                return "Как рассказать о планах на фильмы?"
            elif any(word in text_lower for word in ['работа', 'учёба', 'занятия']):
                return "Как рассказать о своих планах?"
            elif any(word in text_lower for word in ['встреча', 'друзья', 'гулять']):
                return "Как рассказать о встрече с друзьями?"
        
        elif any(word in text_lower for word in ['думаю', 'считаю', 'мнение']):
            return "Как спросить мнение человека?"
        
        elif len(text) < 20:
            return "Что ответить коротко в чате?"
        
        elif len(text) > 100:
            return "Как развернуто ответить на вопрос?"
        
        else:
            # Универсальные вопросы в зависимости от длины
            if len(text) < 50:
                return "Что ответить в диалоге?"
            else:
                return "Как продолжить разговор?"
    
    @staticmethod
    def detect_conversation_type(text, dialog_name):
        """Определяет тип беседы для более точных вопросов"""
        text_lower = text.lower()
        dialog_lower = dialog_name.lower()
        
        # Определяем контекст по содержанию и имени диалога
        if any(word in text_lower for word in ['работа', 'проект', 'задача', 'начальник']):
            return "рабочий"
        elif any(word in text_lower or word in dialog_lower for word in ['друг', 'подруга', 'брат', 'сестра', 'папа', 'мама']):
            return "личный"
        elif any(word in text_lower for word in ['учеба', 'преподаватель', 'занятия', 'лекция']):
            return "учебный"
        elif any(word in text_lower for word in ['игра', 'гейм', 'steam', 'playstation']):
            return "игровой"
        else:
            return "обычный"

class TelegramDataCollector:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.client = None
        self.question_gen = QuestionGenerator()
        
    async def init_client(self):
        """Инициализация клиента Telethon"""
        session_name = f"user_{self.user_id}"
        self.client = TelegramClient(session_name, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone)
        print(f"✅ Клиент Telegram авторизован для пользователя {self.user_id}")
    
    async def has_my_messages(self, dialog_id, preview_limit=50):
        """Проверяем есть ли мои сообщения в первых preview_limit сообщениях чата"""
        me = await self.client.get_me()
        my_id = me.id
        
        message_count = 0
        async for message in self.client.iter_messages(dialog_id, limit=preview_limit):
            if (message.text and 
                len(message.text.strip()) > 1 and
                hasattr(message, 'sender_id') and 
                message.sender_id == my_id):
                return True
            message_count += 1
        
        return False
    
    async def collect_messages_from_dialog(self, dialog, deep_limit=1000, preview_limit=50):
        """Сбор сообщений из одного диалога с оптимизацией"""
        me = await self.client.get_me()
        my_id = me.id
        dialog_name = get_display_name(dialog.entity)
        
        print(f"🔍 Проверяем чат: {dialog_name}")
        
        # Сначала проверяем первые preview_limit сообщений
        has_my_messages = await self.has_my_messages(dialog.id, preview_limit)
        
        if not has_my_messages:
            print(f"   ⏩ Пропускаем (нет моих сообщений в первых {preview_limit})")
            return []
        
        print(f"   ✅ Найдены мои сообщения, собираем глубоко...")
        
        # Если есть мои сообщения, собираем глубоко
        messages = []
        message_count = 0
        
        async for message in self.client.iter_messages(dialog.id, limit=deep_limit):
            if (message.text and 
                len(message.text.strip()) > 1 and
                hasattr(message, 'sender_id') and 
                message.sender_id == my_id):
                
                # Очищаем текст от лишних пробелов
                clean_text = re.sub(r'\s+', ' ', message.text.strip())
                
                messages.append({
                    'text': clean_text,
                    'date': message.date.isoformat(),
                    'dialog_with': dialog_name,
                    'message_id': message.id,
                    'length': len(clean_text)
                })
                message_count += 1
        
        print(f"   📝 Собрано сообщений: {message_count}")
        return messages
    
    async def collect_all_messages_optimized(self, deep_limit=1000, preview_limit=50):
        """Основной метод сбора с оптимизацией"""
        print(f"🚀 Запускаем оптимизированный сбор сообщений...")
        print(f"   • Предпросмотр: первые {preview_limit} сообщений")
        print(f"   • Глубокий сбор: до {deep_limit} сообщений")
        
        me = await self.client.get_me()
        my_id = me.id
        print(f"👤 ID вашего аккаунта: {my_id}")
        
        # Собираем все диалоги
        all_dialogs = []
        async for dialog in self.client.iter_dialogs():
            all_dialogs.append(dialog)
        
        print(f"📂 Найдено диалогов: {len(all_dialogs)}")
        
        all_messages = []
        stats = {
            'total_dialogs': len(all_dialogs),
            'checked_dialogs': 0,
            'skipped_no_messages': 0,
            'collected_dialogs': 0,
            'total_messages': 0
        }
        
        # Обрабатываем каждый диалог
        for i, dialog in enumerate(all_dialogs):
            stats['checked_dialogs'] += 1
            print(f"\n[{i+1}/{len(all_dialogs)}] ", end="")
            
            messages = await self.collect_messages_from_dialog(
                dialog, 
                deep_limit=deep_limit, 
                preview_limit=preview_limit
            )
            
            if messages:
                stats['collected_dialogs'] += 1
                stats['total_messages'] += len(messages)
                all_messages.extend(messages)
            else:
                stats['skipped_no_messages'] += 1
        
        # Выводим статистику
        print(f"\n📊 СБОР ЗАВЕРШЕН:")
        print(f"   • Проверено диалогов: {stats['checked_dialogs']}")
        print(f"   • Пропущено (нет сообщений): {stats['skipped_no_messages']}")
        print(f"   • Обработано (с сообщениями): {stats['collected_dialogs']}")
        print(f"   • Всего сообщений: {stats['total_messages']}")
        
        return all_messages
    
    def create_training_examples_with_questions(self, messages):
        """Создание обучающих примеров с сгенерированными вопросами"""
        training_examples = []
        
        if not messages:
            return training_examples
            
        for i, message in enumerate(messages):
            text = message['text']
            dialog_name = message['dialog_with']
            
            # Генерируем контекстный вопрос
            question = self.question_gen.generate_question_for_answer(text)
            
            # Определяем тип беседы для более точного контекста
            conv_type = self.question_gen.detect_conversation_type(text, dialog_name)
            
            # Создаем пример в формате instruction-input-output
            training_example = {
                "instruction": question,
                "input": f"Контекст: {conv_type} чат с {dialog_name}",
                "output": text,
                "metadata": {
                    "date": message['date'],
                    "dialog_with": dialog_name,
                    "conversation_type": conv_type,
                    "original_text": text[:100] + "..." if len(text) > 100 else text,
                    "generated_question": question
                }
            }
            
            training_examples.append(training_example)
            
            # Добавляем дополнительный вариант с другим вопросом
            if i % 3 == 0:  # Каждое третье сообщение получает дополнительный пример
                alt_question = self.create_alternative_question(text, conv_type)
                alt_example = {
                    "instruction": alt_question,
                    "input": f"Ситуация: {conv_type} общение",
                    "output": text,
                    "metadata": {
                        "date": message['date'],
                        "dialog_with": dialog_name,
                        "conversation_type": conv_type,
                        "original_text": text[:100] + "..." if len(text) > 100 else text,
                        "generated_question": alt_question
                    }
                }
                training_examples.append(alt_example)
        
        return training_examples
    
    def create_alternative_question(self, text, conv_type):
        """Создает альтернативный вопрос для разнообразия данных"""
        text_lower = text.lower()
        
        if conv_type == "рабочий":
            alternatives = [
                "Как ответить коллеге?",
                "Что написать в рабочем чате?",
                "Как профессионально ответить?"
            ]
        elif conv_type == "личный":
            alternatives = [
                "Как ответить другу?",
                "Что написать близкому человеку?",
                "Как поддержать разговор с другом?"
            ]
        elif conv_type == "учебный":
            alternatives = [
                "Как ответить в учебном чате?",
                "Что написать одногруппнику?",
                "Как обсудить учебные вопросы?"
            ]
        else:
            alternatives = [
                "Как продолжить диалог?",
                "Что ответить в переписке?",
                "Как поддержать беседу?"
            ]
        
        import random
        return random.choice(alternatives)
    
    def create_chatml_format_with_context(self, messages):
        """Создание данных в формате ChatML с контекстом"""
        chat_examples = []
        
        if not messages:
            return chat_examples
            
        for message in messages:
            text = message['text']
            dialog_name = message['dialog_with']
            conv_type = self.question_gen.detect_conversation_type(text, dialog_name)
            question = self.question_gen.generate_question_for_answer(text)
            
            chat_example = {
                "messages": [
                    {
                        "role": "system", 
                        "content": f"Ты общаешься в {conv_type} чате с {dialog_name}. Твой стиль общения должен соответствовать твоим историческим сообщениям."
                    },
                    {
                        "role": "user", 
                        "content": question
                    },
                    {
                        "role": "assistant",
                        "content": text
                    }
                ],
                "metadata": {
                    "dialog_with": dialog_name,
                    "conversation_type": conv_type,
                    "generated_question": question
                }
            }
            
            chat_examples.append(chat_example)
        
        return chat_examples
    
    async def save_training_data(self, raw_messages, training_examples, chatml_examples):
        """Сохранение данных в разных форматах"""
        user_dir = f"user_data/{self.user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        # Сохраняем сырые сообщения
        raw_filename = f"{user_dir}/raw_personal_messages.json"
        with open(raw_filename, 'w', encoding='utf-8') as f:
            json.dump(raw_messages, f, ensure_ascii=False, indent=2)
        
        # Сохраняем данные в формате Alpaca с вопросами
        training_filename = f"{user_dir}/training_data_alpaca.json"
        with open(training_filename, 'w', encoding='utf-8') as f:
            json.dump(training_examples, f, ensure_ascii=False, indent=2)
        
        # Сохраняем данные в формате ChatML
        chatml_filename = f"{user_dir}/training_data_chatml.json"
        with open(chatml_filename, 'w', encoding='utf-8') as f:
            json.dump(chatml_examples, f, ensure_ascii=False, indent=2)
        
        # Статистика
        stats = {
            'user_id': self.user_id,
            'total_raw_messages': len(raw_messages),
            'training_examples': len(training_examples),
            'chatml_examples': len(chatml_examples),
            'average_message_length': sum(msg['length'] for msg in raw_messages) / len(raw_messages) if raw_messages else 0,
            'dialogs_count': len(set(msg['dialog_with'] for msg in raw_messages)),
            'conversation_types': {}
        }
        
        # Анализируем типы бесед
        for example in training_examples:
            conv_type = example['metadata']['conversation_type']
            stats['conversation_types'][conv_type] = stats['conversation_types'].get(conv_type, 0) + 1
        
        stats_filename = f"{user_dir}/dataset_stats.json"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Данные сохранены:")
        print(f"   • Сырые сообщения: {len(raw_messages)}")
        print(f"   • Alpaca примеров: {len(training_examples)}")
        print(f"   • ChatML примеров: {len(chatml_examples)}")
        print(f"   • Типы бесед: {stats['conversation_types']}")
        
        return {
            'raw_file': raw_filename,
            'training_file': training_filename,
            'chatml_file': chatml_filename,
            'stats_file': stats_filename
        }
    
    async def collect_and_save(self):
        """Полный процесс сбора и преобразования данных"""
        try:
            await self.init_client()
            
            # Используем оптимизированный сбор
            raw_messages = await self.collect_all_messages_optimized(
                deep_limit=1000, 
                preview_limit=50
            )
            
            if not raw_messages:
                print("❌ Не найдено сообщений для обработки")
                await self.client.disconnect()
                return {
                    'success': False,
                    'error': 'Не найдено сообщений в чатах',
                    'message_count': 0,
                    'raw_messages_count': 0,
                    'training_examples_count': 0,
                    'chatml_examples_count': 0
                }
            
            # Преобразуем в форматы для обучения с вопросами
            print("\n🔄 Генерация обучающих данных с вопросами...")
            
            training_examples = self.create_training_examples_with_questions(raw_messages)
            print(f"✅ Alpaca примеров с вопросами: {len(training_examples)}")
            
            chatml_examples = self.create_chatml_format_with_context(raw_messages)
            print(f"✅ ChatML примеров с контекстом: {len(chatml_examples)}")
            
            # Сохраняем все форматы
            data_files = await self.save_training_data(raw_messages, training_examples, chatml_examples)
            
            await self.client.disconnect()
            
            print(f"\n🎉 Сбор и генерация данных завершены!")
            print(f"📊 Увеличено примеров в {len(training_examples)/len(raw_messages):.1f} раз")
            
            return {
                'success': True,
                'user_id': self.user_id,
                'raw_messages_count': len(raw_messages),
                'training_examples_count': len(training_examples),
                'chatml_examples_count': len(chatml_examples),
                'files': data_files
            }
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return {
                'success': False,
                'error': str(e),
                'message_count': 0,
                'raw_messages_count': 0,
                'training_examples_count': 0,
                'chatml_examples_count': 0
            }

async def main():
    user_id = "6209265331"
    
    print("🚀 ЗАПУСК ОПТИМИЗИРОВАННОГО СБОРА С ВОПРОСАМИ...")
    collector = TelegramDataCollector(user_id)
    result = await collector.collect_and_save()
    
    if result and result.get('success'):
        print(f"✅ Успешно! Собрано {result['raw_messages_count']} сообщений")
        print(f"✅ Сгенерировано {result['training_examples_count']} обучающих примеров")
    else:
        print(f"❌ Сбор не удался: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())