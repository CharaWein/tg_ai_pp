# master_bot.py
import os
import logging
import json
import asyncio
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import sys
import subprocess
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(__file__))

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MasterBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.training_status = {}
    
    def save_share_link(self, user_id: str, clone_name: str, token: str):
        """Сохраняет ссылку в файл для сервера клонов"""
        try:
            links_file = "clone_links.json"
            links = {}
            
            # Загружаем существующие ссылки
            if os.path.exists(links_file):
                with open(links_file, 'r', encoding='utf-8') as f:
                    links = json.load(f)
            
            # Добавляем новую ссылку
            links[token] = {
                'user_id': user_id,
                'name': clone_name,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            # Сохраняем обратно
            with open(links_file, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Ссылка сохранена в файл: {token}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ссылки: {e}")

    def get_share_service(self):
        """Получить сервис для генерации ссылок"""
        try:
            from clone_server import share_service
            return share_service
        except ImportError:
            # Запасной вариант с сохранением в файл
            class FileShareService:
                def __init__(self, master_bot):
                    self.master_bot = master_bot
                    self.links = {}
                
                def generate_share_link(self, user_id, clone_name):
                    token = str(uuid.uuid4())
                    
                    # Сохраняем в файл через master_bot
                    self.master_bot.save_share_link(user_id, clone_name, token)
                    
                    return token
                
                def get_all_links(self):
                    try:
                        links_file = "clone_links.json"
                        if os.path.exists(links_file):
                            with open(links_file, 'r', encoding='utf-8') as f:
                                links = json.load(f)
                            return {k: v for k, v in links.items() if v.get('active', True)}
                        return {}
                    except:
                        return {}
            
            return FileShareService(self)  # Передаем self (master_bot) в конструктор

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок бота"""
        logger.error(f"Ошибка в боте: {context.error}", exc_info=context.error)
        
        # Можно отправить сообщение пользователю об ошибке
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
                )
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "🤖 Добро пожаловать в AI Clone Bot!\n\n"
            "Этот бот создаст вашу AI-копию на основе ваших сообщений.\n\n"
            "Доступные команды:\n"
            "/collect_data - Собрать данные для обучения\n"
            "/train_ai - Обучить AI-клон\n"
            "/get_link - Получить ссылку на клона\n"
            "/status - Статус обучения\n\n"
            "Начните с команды /collect_data"
        )

    async def collect_data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /collect_data"""
        user_id = str(update.effective_user.id)
        await update.message.reply_text(
            "📊 Собираем ваши сообщения для обучения...\n\n"
            "Это может занять несколько минут.\n"
            "Пожалуйста, подождите..."
        )
        
        # Здесь должна быть логика сбора данных
        # Пока просто заглушка
        await asyncio.sleep(2)
        await update.message.reply_text(
            "✅ Данные собраны! Теперь можно обучать модель командой /train_ai"
        )

    async def get_link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /get_link"""
        user_id = str(update.effective_user.id)
        model_path = f"trained_models/user_{user_id}"
        
        if not os.path.exists(model_path):
            await update.message.reply_text(
                "❌ У вас еще нет обученного AI-клона.\n"
                "Сначала выполните /train_ai для обучения модели."
            )
            return
        
        # Генерируем или получаем существующую ссылку
        share_service = self.get_share_service()
        user_name = update.effective_user.first_name
        clone_name = f"AI Клон {user_name}"
        token = share_service.generate_share_link(user_id, clone_name)
        web_url = f"http://localhost:8001/clone/{token}/web"
        
        await update.message.reply_text(
            f"🔗 Ваша ссылка на AI-клона:\n\n{web_url}\n\n"
            f"💡 Поделитесь этой ссылкой, чтобы другие могли пообщаться с вашим AI-клоном!"
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /status"""
        user_id = str(update.effective_user.id)
        model_path = f"trained_models/user_{user_id}"
        
        if os.path.exists(model_path):
            await update.message.reply_text(
                "✅ У вас есть обученный AI-клон!\n"
                "Используйте /get_link для получения ссылки."
            )
        else:
            await update.message.reply_text(
                "❌ У вас еще нет обученного AI-клона.\n\n"
                "Шаги для создания:\n"
                "1. /collect_data - собрать данные\n"
                "2. /train_ai - обучить модель\n"
                "3. /get_link - получить ссылку"
            )

    async def train_ai_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обучение AI модели через отдельный скрипт"""
        user_id = str(update.effective_user.id)
        user_name = update.effective_user.first_name
        
        # Проверяем существующую модель
        model_path = f"trained_models/user_{user_id}"
        if os.path.exists(model_path):
            await update.message.reply_text(
                "✅ У вас уже есть обученный AI-клон!\n"
                "Используйте /get_link для получения ссылки."
            )
            return

        progress_msg = await update.message.reply_text(
            "🧠 Запускаем обучение AI-клона...\n"
            "⏳ Ожидаемое время: 3-7 минут\n\n"
            "⚡ Используем русские модели\n"
            "📝 Обучаем на ваших сообщениях\n"
            "🎯 2 эпохи обучения\n\n"
            "Этапы:\n"
            "1. Подготовка данных...\n"
            "2. Загрузка модели...\n"
            "3. Обучение...\n"
            "4. Сохранение..."
        )
        
        try:
            # Проверяем наличие данных
            data_file = f"user_data/{user_id}/training_data_alpaca.json"
            if not os.path.exists(data_file):
                await progress_msg.edit_text("❌ Данные не найдены. Сначала выполните /collect_data")
                return
            
            # Запускаем обучение в отдельном процессе
            await progress_msg.edit_text(
                "🔧 Запускаем процесс обучения...\n"
                "📊 Подготавливаем данные..."
            )
            
            # Используем отдельный скрипт обучения
            def run_training():
                from model_trainer import train_user_model
                return train_user_model(user_id)
            
            # Запускаем в отдельном потоке
            loop = asyncio.get_event_loop()
            training_results = await loop.run_in_executor(None, run_training)
            
            if not training_results["success"]:
                await progress_msg.edit_text(
                    f"❌ Обучение не удалось:\n{training_results['message']}\n\n"
                    f"💡 Попробуйте:\n"
                    f"• Собрать больше данных /collect_data\n"
                    f"• Подождать и попробовать снова\n"
                    f"• Проверить интернет соединение"
                )
                return
            
            # Создаем ссылку на клон
            share_service = self.get_share_service()
            clone_name = f"AI Клон {user_name}"
            token = share_service.generate_share_link(user_id, clone_name)
            web_url = f"http://localhost:8001/clone/{token}/web"
            
            total_minutes = training_results['training_time'] / 60
            
            await progress_msg.edit_text(
                f"🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!\n\n"
                f"👤 {user_name}, ваш AI-клон готов!\n\n"
                f"📊 Результаты:\n"
                f"• Модель: {training_results.get('base_model', 'Russian GPT')}\n"
                f"• Время: {total_minutes:.1f} минут\n"
                f"• Примеров: {training_results['samples_used']}\n\n"
                f"🌐 Ваша ссылка:\n{web_url}\n\n"
                f"💡 Общайтесь с вашей AI-копией!"
            )
                
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}")
            await progress_msg.edit_text(
                f"❌ Ошибка обучения:\n{str(e)}\n\n"
                f"Попробуйте позже или обратитесь к разработчику."
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
        
        print("🤖 Запускаем AI Clone Bot...")
        print("🧠 Русские модели: rugpt3small, ruDialoGPT")
        print("⚡ Обучение за 3-7 минут") 
        print("🎯 Сбор личных сообщений")
        print("✅ Бот запущен! Напишите /start в Telegram")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    main()