# master_bot.py
import os
import logging
import json
import asyncio
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys

sys.path.append(os.path.dirname(__file__))

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class OpenLlamaTrainer:
    """Тренер для открытых моделей в стиле Llama"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.available_models = [
            "microsoft/DialoGPT-medium",  # Легкая модель для чатов
            "microsoft/DialoGPT-large",   # Более качественная
            "facebook/blenderbot-400M-distill",  # Хорошая для диалогов
            "IlyaGusev/fred-t5-ru-turbo",  # Русскоязычная
            "ai-forever/rugpt3large_based_on_gpt2"  # Русская GPT
        ]
        
    def load_model(self, model_index: int = 0):
        """Загрузка модели и токенизатора"""
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            model_name = self.available_models[model_index]
            logger.info(f"🔄 Загружаем модель: {model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("✅ Модель успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели {self.available_models[model_index]}: {e}")
            
            # Пробуем следующую модель
            if model_index + 1 < len(self.available_models):
                logger.info(f"🔄 Пробуем следующую модель: {self.available_models[model_index + 1]}")
                return self.load_model(model_index + 1)
            else:
                logger.error("❌ Все модели недоступны")
                return False
    
    def prepare_training_data(self, training_data: List[Dict]) -> List[Dict]:
        """Подготовка данных для обучения"""
        formatted_data = []
        
        for item in training_data:
            if not item.get('text') or len(item['text'].strip()) < 10:
                continue
                
            text = item['text'].strip()
            
            # Форматируем для диалоговой модели
            if "dialo" in self.tokenizer.name_or_path.lower() or "blender" in self.tokenizer.name_or_path.lower():
                # Для диалоговых моделей
                formatted_text = f"User: {text}\nBot:"
            elif "gpt" in self.tokenizer.name_or_path.lower():
                # Для GPT-стиля моделей
                formatted_text = f"Пользователь: {text}\nАссистент:"
            else:
                # Универсальный формат
                formatted_text = text
            
            encoded = self.tokenizer(
                formatted_text,
                truncation=True,
                max_length=256,  # Укоротили для стабильности
                padding=False,
                return_tensors=None
            )
            
            formatted_data.append({
                "input_ids": encoded["input_ids"],
                "attention_mask": encoded["attention_mask"],
                "labels": encoded["input_ids"].copy()
            })
        
        return formatted_data
    
    def train_model(self, user_id: str, training_data: List[Dict]) -> Dict[str, Any]:
        """Обучение модели"""
        try:
            import torch
            from peft import LoraConfig, get_peft_model, TaskType
            from transformers import TrainingArguments, Trainer
            
            start_time = time.time()
            
            # Проверяем данные
            if len(training_data) < 3:
                return {
                    "success": False,
                    "message": f"Недостаточно данных: {len(training_data)} сообщений (требуется минимум 3)",
                    "training_time": 0,
                    "samples_used": 0
                }
            
            # Загружаем модель если еще не загружена
            if self.model is None:
                if not self.load_model():
                    return {
                        "success": False,
                        "message": "Не удалось загрузить ни одну модель",
                        "training_time": 0,
                        "samples_used": 0
                    }
            
            # Подготавливаем данные
            formatted_data = self.prepare_training_data(training_data)
            if not formatted_data:
                return {
                    "success": False,
                    "message": "Не удалось подготовить данные для обучения",
                    "training_time": 0,
                    "samples_used": 0
                }
            
            # Настраиваем LoRA если модель поддерживает
            try:
                lora_config = LoraConfig(
                    task_type=TaskType.CAUSAL_LM,
                    inference_mode=False,
                    r=8,
                    lora_alpha=32,
                    lora_dropout=0.1,
                    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "c_proj"]
                )
                model = get_peft_model(self.model, lora_config)
                use_lora = True
            except:
                model = self.model
                use_lora = False
                logger.info("⚠️ LoRA не поддерживается, используем полное обучение")
            
            # Параметры обучения
            training_args = TrainingArguments(
                output_dir=f"trained_models/user_{user_id}",
                overwrite_output_dir=True,
                num_train_epochs=2,
                per_device_train_batch_size=1,
                gradient_accumulation_steps=4,
                warmup_steps=20,
                logging_steps=5,
                save_steps=50,
                learning_rate=1e-4,
                fp16=torch.cuda.is_available(),
                optim="adamw_torch",
                remove_unused_columns=False,
                dataloader_pin_memory=False,
            )
            
            # Создаем тренер
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=formatted_data,
                tokenizer=self.tokenizer,
            )
            
            # Запускаем обучение
            logger.info(f"🚀 Начинаем обучение на {len(formatted_data)} примерах...")
            trainer.train()
            
            # Сохраняем модель
            trainer.save_model()
            self.tokenizer.save_pretrained(f"trained_models/user_{user_id}")
            
            training_time = time.time() - start_time
            
            method = "LoRA" if use_lora else "Full"
            
            return {
                "success": True,
                "message": f"Модель успешно обучена на {len(formatted_data)} примерах ({method})",
                "model_path": f"trained_models/user_{user_id}",
                "training_time": round(training_time, 2),
                "samples_used": len(formatted_data),
                "method": method
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обучения: {e}")
            return {
                "success": False,
                "message": f"Ошибка обучения: {str(e)}",
                "training_time": 0,
                "samples_used": 0
            }

class MasterBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.training_status = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = """
🤖 Добро пожаловать в Open AI Clone Creator!

Я создаю вашу точную AI-копию на основе открытых моделей.

🚀 **ОТКРЫТАЯ ВЕРСИЯ:**
- Обучение на открытых моделях (не требует доступа)
- Технология LoRA для быстрой адаптации  
- Автоматический выбор лучшей модели
- Поддержка русского и английского

**Команды:**
/collect_data - 📥 Собрать мои сообщения из Telegram
/train_ai - 🧠 Обучить AI-клон (5-15 мин)
/get_link - 🔗 Получить ссылку на веб-чат
/status - 📊 Статус обучения

**Процесс:**
1. Сбор сообщений (2-5 минут)
2. Очистка и подготовка данных
3. Быстрое дообучение (5-15 минут) 
4. Получение ссылки на веб-интерфейс

Начните с /collect_data
        """
        await update.message.reply_text(welcome_text)

    async def collect_data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сбор данных пользователя"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        progress_msg = await update.message.reply_text(
            "📥 Запускаем сбор ваших сообщений...\n"
            "⏳ Это займет 2-5 минут...\n\n"
            "🔍 Сканируем диалоги...\n"
            "📝 Собираем сообщения...\n"
            "💾 Сохраняем данные..."
        )
        
        try:
            from data_collector import TelegramDataCollector
            collector = TelegramDataCollector(user_id)
            result = await collector.collect_and_save()
            
            if not result.get('success'):
                error_msg = result.get('error', 'Неизвестная ошибка')
                await progress_msg.edit_text(
                    f"❌ Ошибка сбора данных:\n{error_msg}\n\n"
                    f"Проверьте настройки Telegram API в .env файле."
                )
                return
            
            # Показываем результаты
            message_count = result['message_count']
            cleaned_count = result.get('cleaned_count', message_count)
            
            quality_indicator = "👍" if cleaned_count > 10 else "👎" if cleaned_count > 3 else "❌"
            
            await progress_msg.edit_text(
                f"✅ Сбор данных завершен, {user_name}!\n\n"
                f"📊 Результаты:\n"
                f"• Собрано сообщений: {message_count}\n"
                f"• После очистки: {cleaned_count}\n"
                f"• Качество данных: {quality_indicator}\n\n"
                f"{'🎯 Отлично! Можно обучать AI-клон!' if cleaned_count > 10 else '⚠️ Мало данных, но можно попробовать' if cleaned_count > 3 else '❌ Слишком мало данных для обучения'}\n\n"
                f"Отправьте /train_ai чтобы начать обучение."
            )
            
        except Exception as e:
            logger.error(f"Ошибка сбора данных: {e}")
            await progress_msg.edit_text(
                f"❌ Критическая ошибка при сборе данных:\n{str(e)}\n\n"
                f"Попробуйте позже или проверьте настройки."
            )

    async def train_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обучение AI модели"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # Проверяем существующую модель
        model_path = f"trained_models/user_{user_id}"
        if os.path.exists(model_path):
            await update.message.reply_text(
                "✅ У вас уже есть обученный AI-клон!\n"
                "Используйте /get_link для получения ссылки.\n\n"
                "Для переобучения удалите папку:\n"
                f"`trained_models/user_{user_id}`"
            )
            return

        progress_msg = await update.message.reply_text(
            "🧠 Запускаем обучение AI модели...\n"
            "⏳ Ожидаемое время: 5-15 минут\n\n"
            "🎯 Этапы обучения:\n"
            "1. Поиск доступной модели...\n"
            "2. Настройка адаптера...\n" 
            "3. Подготовка данных...\n"
            "4. Быстрое обучение...\n"
            "5. Сохранение модели..."
        )
        
        try:
            # Загрузка данных
            data_file = f"user_data/{user_id}/training_data.json"
            if not os.path.exists(data_file):
                await progress_msg.edit_text("❌ Данные для обучения не найдены.")
                return
            
            with open(data_file, 'r', encoding='utf-8') as f:
                user_messages = json.load(f)
            
            await progress_msg.edit_text(
                f"📊 Загружено {len(user_messages)} сообщений\n"
                "🔍 Ищем доступную модель...\n"
                "⚡ Настраиваем обучение...\n"
                "🧠 Подготавливаем данные..."
            )
            
            # Используем Open тренер
            trainer = OpenLlamaTrainer()
            
            # Запускаем обучение в отдельном потоке
            def train_wrapper():
                return trainer.train_model(user_id, user_messages)
            
            loop = asyncio.get_event_loop()
            training_results = await loop.run_in_executor(None, train_wrapper)
            
            if not training_results["success"]:
                await progress_msg.edit_text(
                    f"❌ Ошибка обучения:\n{training_results['message']}\n\n"
                    f"Попробуйте собрать больше данных /collect_data"
                )
                return
            
            # Создаем ссылку для доступа
            share_service = self.get_share_service()
            clone_name = f"AI Клон {user_name}"
            token = share_service.generate_share_link(user_id, clone_name)
            web_url = f"http://localhost:8001/clone/{token}/web"
            
            total_minutes = training_results['training_time'] / 60
            
            await progress_msg.edit_text(
                f"🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО, {user_name}!\n\n"
                f"⏱️ Время обучения: {total_minutes:.1f} минут\n"
                f"📊 Результаты:\n"
                f"• Сообщений: {len(user_messages)}\n"
                f"• Обучающих примеров: {training_results['samples_used']}\n"
                f"• Метод: {training_results.get('method', 'Standard')}\n\n"
                f"🌐 Ваша ссылка для чата:\n{web_url}\n\n"
                f"💡 Перейдите по ссылке чтобы пообщаться с вашим AI-клоном!"
            )
                
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}")
            await progress_msg.edit_text(
                f"❌ Ошибка при обучении:\n{str(e)}\n\n"
                f"Возможные причины:\n"
                f"• Недостаточно данных (< 3 сообщений)\n"
                f"• Проблемы с памятью\n"
                f"• Ошибка загрузки моделей\n\n"
                f"Попробуйте:\n"
                f"1. Собрать больше данных /collect_data\n"
                f"2. Перезапустить бота\n"
                f"3. Проверить интернет соединение"
            )

    async def get_link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить ссылку на клон"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        try:
            share_service = self.get_share_service()
            
            # Проверяем есть ли обученная модель
            model_path = f"trained_models/user_{user_id}"
            
            if not os.path.exists(model_path):
                await update.message.reply_text(
                    "❌ У вас еще нет обученного AI-клона.\n\n"
                    "Сначала:\n"
                    "1. Соберите данные /collect_data\n" 
                    "2. Обучите модель /train_ai\n\n"
                    "Обучение займет 5-15 минут ⚡"
                )
                return
            
            # Ищем существующую активную ссылку
            existing_links = share_service.get_all_links()
            user_link = None
            
            for token, info in existing_links.items():
                if info.get('user_id') == user_id and info.get('active', True):
                    user_link = f"http://localhost:8001/clone/{token}/web"
                    break
            
            if user_link:
                await update.message.reply_text(
                    f"🔗 Ваш AI-клон готов, {user_name}!\n\n"
                    f"{user_link}\n\n"
                    f"💡 Перейдите по ссылке чтобы пообщаться с вашей AI-копией!"
                )
            else:
                # Создаем новую ссылку
                clone_name = f"AI Клон {user_name}"
                token = share_service.generate_share_link(user_id, clone_name)
                user_link = f"http://localhost:8001/clone/{token}/web"
                
                await update.message.reply_text(
                    f"🔗 Создана новая ссылка, {user_name}!\n\n"
                    f"{user_link}\n\n"
                    f"🎉 Ваш AI-клон ждет общения!"
                )
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка получения ссылки:\n{str(e)}\n\n"
                f"Попробуйте обучить модель заново /train_ai"
            )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статус обучения"""
        user_id = str(update.effective_user.id)
        
        # Проверяем данные
        data_file = f"user_data/{user_id}/training_data.json"
        has_data = os.path.exists(data_file)
        data_count = 0
        if has_data:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data_count = len(data)
        
        # Проверяем модель
        model_path = f"trained_models/user_{user_id}"
        has_model = os.path.exists(model_path)
        
        # Проверяем ссылки
        share_service = self.get_share_service()
        user_links = []
        for token, info in share_service.get_all_links().items():
            if info.get('user_id') == user_id:
                user_links.append(f"http://localhost:8001/clone/{token}/web")
        
        status_text = (
            f"📊 Статус вашего AI-клона:\n\n"
            f"📝 Данные: {'✅' if has_data else '❌'}\n"
            f"   • Сообщений: {data_count}\n\n"
            f"🧠 Модель: {'✅' if has_model else '❌'}\n"
            f"   • Открытая архитектура\n\n"
            f"🔗 Ссылки: {len(user_links)} активных\n"
        )
        
        if user_links:
            status_text += f"\n🌐 Ваши ссылки:\n" + "\n".join(user_links)
        
        if not has_data:
            status_text += "\n🎯 Действие: /collect_data - собрать данные"
        elif not has_model:
            status_text += "\n🎯 Действие: /train_ai - обучить модель (5-15 мин)"
        else:
            status_text += "\n🎯 Действие: /get_link - получить ссылку"
        
        await update.message.reply_text(status_text)

    def get_share_service(self):
        """Получить сервис для генерации ссылок"""
        try:
            from clone_server import share_service
            return share_service
        except ImportError:
            # Запасной вариант
            class SimpleShareService:
                def __init__(self):
                    self.links = {}
                
                def generate_share_link(self, user_id, clone_name):
                    import uuid
                    token = str(uuid.uuid4())
                    self.links[token] = {
                        'user_id': user_id,
                        'name': clone_name,
                        'active': True
                    }
                    return token
                
                def get_all_links(self):
                    return {k: v for k, v in self.links.items() if v.get('active', True)}
            
            return SimpleShareService()

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Ошибка: {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже или обратитесь к разработчику."
            )

# Создаём экземпляр бота
master_bot = MasterBot()

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.start_command(update, context)

async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.collect_data_command(update, context)

async def train_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.train_ai_command(update, context)

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.get_link_command(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.status_command(update, context)

def main():
    if not master_bot.bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
        return
    
    try:
        application = Application.builder().token(master_bot.bot_token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("collect_data", collect_data))
        application.add_handler(CommandHandler("train_ai", train_ai))
        application.add_handler(CommandHandler("get_link", get_link))
        application.add_handler(CommandHandler("status", status))
        
        # Обработчик ошибок
        application.add_error_handler(master_bot.error_handler)
        
        print("🤖 Запускаем Open AI Master Bot...")
        print("🧠 Обучение на открытых моделях")
        print("⚡ Быстрое обучение за 5-15 минут") 
        print("🌐 Автоматический выбор моделей")
        print("✅ Бот запущен! Напишите /start в Telegram")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()