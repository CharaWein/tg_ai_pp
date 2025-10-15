import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class PersonalStyleBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Загружаем вашу обученную модель
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("./my_style_model")
            self.model = AutoModelForCausalLM.from_pretrained("./my_style_model")
            self.personal_style = True
            print("✅ Загружена ваша персональная модель!")
        except:
            self.personal_style = False
            print("⚠️ Используется стандартная модель")
    
    def generate_personal_response(self, message):
        """Генерация ответа вашим стилем"""
        prompt = f"Пользователь: {message}\nТы:"
        
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=150,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Извлекаем только ответ бота
        if "Ты:" in response:
            return response.split("Ты:")[-1].strip()
        return response

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Привет! Я бот, обученный на стиле общения моего создателя. "
        "Поговори со мной как будто это он!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot_data['personal_bot']
    user_message = update.message.text
    
    if bot.personal_style:
        response = bot.generate_personal_response(user_message)
    else:
        # Запасной вариант
        response = "Извините, персональная модель ещё не готова"
    
    await update.message.reply_text(response)

def main():
    bot = PersonalStyleBot()
    
    application = Application.builder().token(bot.bot_token).build()
    application.bot_data['personal_bot'] = bot
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Персональный бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()