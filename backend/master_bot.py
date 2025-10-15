import os
import logging
import json
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

import uuid
from datetime import datetime

class SimpleShareService:
    def __init__(self):
        self.links = {}
    
    def generate_share_link(self, user_id: str, clone_name: str) -> str:
        """Простая генерация ссылки"""
        try:
            # Деактивируем старые ссылки
            for token, info in list(self.links.items()):
                if info.get('user_id') == user_id:
                    info['active'] = False
            
            # Создаем новую ссылку
            token = str(uuid.uuid4())
            
            self.links[token] = {
                'user_id': user_id,
                'name': clone_name,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            return f"http://localhost:8001/clone/{token}"
            
        except Exception as e:
            logger.error(f"Ошибка генерации ссылки: {e}")
            return f"http://localhost:8001/clone/{user_id}"
    
    def get_all_links(self):
        """Получение всех активных ссылок"""
        return {k: v for k, v in self.links.items() if v.get('active', True)}

# Создаем глобальный экземпляр
simple_share_service = SimpleShareService()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def safe_import_share_service():
    """Безопасный импорт share_service"""
    try:
        from clone_server import share_service
        return share_service
    except ImportError as e:
        logger.error(f"Ошибка импорта share_service: {e}")
        return None

class MasterBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.training_status = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_text = """
🤖 Добро пожаловать в AI Clone Creator!

Я могу создать вашу точную AI-копию на основе ваших переписок в Telegram.

Доступные команды:
/collect_data - 📥 Собрать мои сообщения  
/train_ai - 🧠 Обучить нейросеть
/get_link - 🔗 Получить ссылку на веб-чат

Процесс создания клона:
1. Сбор ваших сообщений из Telegram
2. Дообучение нейросети на вашем стиле  
3. Получение ссылки на веб-чат с клоном

После обучения вы получите ссылку на веб-интерфейс где можно общаться с вашим AI-клоном!

Начните с команды /collect_data
        """
        await update.message.reply_text(welcome_text)
    
    async def collect_data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Сбор данных пользователя"""
        user_id = str(update.effective_user.id)
        
        await update.message.reply_text(
            "📥 Начинаем сбор ваших сообщений...\n"
            "Это может занять несколько минут.\n"
            "Пожалуйста, подождите..."
        )
        
        try:
            from data_collector import TelegramDataCollector
            collector = TelegramDataCollector(user_id)
            result = await collector.collect_and_save()
            
            await update.message.reply_text(
                f"✅ Сбор данных завершен!\n"
                f"Собрано сообщений: {result['message_count']}\n\n"
                f"Теперь можно начать обучение AI.\n"
                f"Отправьте /train_ai чтобы начать дообучение нейросети."
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка при сборе данных: {e}\n"
                f"Убедитесь, что вы настроили Telegram API в .env файле."
            )
    
    async def train_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обучение AI модели"""
        user_id = str(update.effective_user.id)
        
        try:
            # Проверяем есть ли уже модель
            model_path = f"trained_models/user_{user_id}"
            if os.path.exists(model_path):
                await update.message.reply_text(
                    "✅ У вас уже есть обученный AI-клон!\n"
                    "Используйте /get_link для получения ссылки.\n\n"
                    "Если хотите переобучить, сначала удалите папку:\n"
                    f"`trained_models/user_{user_id}`"
                )
                return

            await update.message.reply_text(
                "🧠 Начинаем дообучение нейросети...\n"
                "⚡ Используем русскую модель с LoRA\n"
                "⏳ Это займет 10-15 минут...\n\n"
                "Статус будет обновляться..."
            )
            
            # Загружаем данные
            data_file = f"user_data/{user_id}/training_data.json"
            if not os.path.exists(data_file):
                await update.message.reply_text("❌ Данные для обучения не найдены.")
                return
            
            with open(data_file, 'r', encoding='utf-8') as f:
                user_messages = json.load(f)
            
            # Обучаем модель
            try:
                from improved_trainer import ImprovedTrainer
                trainer = ImprovedTrainer(model_name="sberbank-ai/rugpt3small_based_on_gpt2")
                trainer.load_model()
                training_results = trainer.train_improved(user_messages, model_path, epochs=4)
                method = "Улучшенное обучение (5 эпох)"
            except ImportError:
                # Запасной вариант
                from simple_trainer import SimpleTrainer
                trainer = SimpleTrainer(model_name="sberbank-ai/rugpt3small_based_on_gpt2")
                trainer.load_model()
                training_results = trainer.train_simple(user_messages, model_path, epochs=4)
                method = "Простое обучение (5 эпох)"
            
            # Создаем ссылку
            share_service = simple_share_service
            clone_name = f"Клон пользователя {update.effective_user.first_name}"
            share_url = share_service.generate_share_link(user_id, clone_name)
            web_url = f"{share_url}/web"
            
            await update.message.reply_text(
                f"🎉 Обучение завершено!\n\n"
                f"📊 Результаты:\n"
                f"• Сообщений: {len(user_messages)}\n"
                f"• Loss: {training_results.get('final_loss', 0.0):.4f}\n\n"
                f"🌐 {web_url}"
            )
                
        except Exception as e:
            logger.error(f"Ошибка при обучении модели: {e}")
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def get_link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить ссылку на клон"""
        user_id = str(update.effective_user.id)
        
        try:
            # Используем простой сервис вместо импорта
            share_service = simple_share_service
            
            # Проверяем есть ли обученная модель
            model_path = f"trained_models/user_{user_id}"
            if not os.path.exists(model_path):
                await update.message.reply_text(
                    "❌ У вас еще нет обученного AI-клона.\n"
                    "Сначала обучите модель командой /train_ai"
                )
                return
            
            # Ищем существующую ссылку
            existing_links = share_service.get_all_links()
            user_link = None
            
            for token, info in existing_links.items():
                if info.get('user_id') == user_id and info.get('active', True):
                    user_link = f"http://localhost:8001/clone/{token}/web"
                    break
            
            if user_link:
                await update.message.reply_text(
                    f"🔗 Ваша ссылка для доступа к AI-клону:\n{user_link}\n\n"
                    f"Перейдите по ссылке чтобы пообщаться с вашим клоном!"
                )
            else:
                # Создаем новую ссылку
                clone_name = f"Клон пользователя {update.effective_user.first_name}"
                share_url = share_service.generate_share_link(user_id, clone_name)
                user_link = f"{share_url}/web"
                await update.message.reply_text(
                    f"🔗 Создана новая ссылка для доступа к AI-клону:\n{user_link}\n\n"
                    f"Перейдите по ссылке чтобы пообщаться с вашим клоном!"
                )
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения ссылки: {e}")

# Создаём экземпляр бота
master_bot = MasterBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.start_command(update, context)

async def collect_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.collect_data_command(update, context)

async def train_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.train_ai_command(update, context)

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await master_bot.get_link_command(update, context)

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
        
        print("🤖 Запускаем Master Bot для создания AI-клонов...")
        print("✅ Бот запущен! Напишите /start в Telegram")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()