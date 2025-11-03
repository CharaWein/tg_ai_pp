# clone_server.py
import os
import json
import logging
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Модели Pydantic
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Класс для управления клонами
class CloneManager:
    def __init__(self):
        self.links_file = "clone_links.json"
        self.links = self.load_links()
        
    def load_links(self) -> dict:
        """Загрузка ссылок из файла"""
        try:
            if os.path.exists(self.links_file):
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    links = json.load(f)
                logger.info(f"✅ Загружено {len(links)} клонов")
                return links
            else:
                logger.info("Файл ссылок не найден, создаем новый")
                return {}
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки ссылок: {e}")
            return {}
    
    def save_links(self):
        """Сохранение ссылок в файл"""
        try:
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(self.links, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ссылок: {e}")
    
    def register_clone(self, user_id: str, clone_name: str) -> str:
        """Регистрация нового клона"""
        try:
            # Деактивируем старые ссылки этого пользователя
            for token, info in self.links.items():
                if info.get('user_id') == user_id:
                    info['active'] = False
            
            # Создаем новую ссылку
            token = str(uuid.uuid4())
            
            self.links[token] = {
                'user_id': user_id,
                'name': clone_name,
                'created_at': datetime.now().isoformat(),
                'active': True,
                'access_count': 0
            }
            
            self.save_links()
            
            logger.info(f"✅ Зарегистрирован клон {clone_name} для user_id {user_id}")
            return token
            
        except Exception as e:
            logger.error(f"❌ Ошибка регистрации клона: {e}")
            raise
    
    def get_clone_info(self, token: str) -> dict:
        """Получение информации о клоне"""
        if token in self.links:
            clone_info = self.links[token]
            if clone_info.get('active', True):
                # Увеличиваем счетчик обращений
                clone_info['access_count'] = clone_info.get('access_count', 0) + 1
                self.save_links()
                return clone_info
        return None
    
    def get_user_id_by_token(self, token: str) -> str:
        """Получение user_id по токену"""
        clone_info = self.get_clone_info(token)
        return clone_info.get('user_id') if clone_info else None
    
    def get_all_clones(self) -> dict:
        """Получение всех активных клонов"""
        return {k: v for k, v in self.links.items() if v.get('active', True)}

# Класс для генерации ответов
class CloneGenerator:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model = None
        self.tokenizer = None
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Загрузка модели для пользователя"""
        try:
            model_path = f"trained_models/user_{self.user_id}"
            
            if not os.path.exists(model_path):
                logger.warning(f"❌ Модель для user_id {self.user_id} не найдена")
                return False
            
            logger.info(f"🔄 Загружаем модель для user_id {self.user_id}")
            
            # Загружаем токенизатор и модель
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path)
            
            # Настраиваем паддинг
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model_loaded = True
            logger.info(f"✅ Модель для user_id {self.user_id} успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            return False
    
    def generate_response(self, message: str) -> str:
        """Генерация ответа от клона"""
        if not self.model_loaded:
            return "Модель не загружена. Попробуйте позже."
        
        try:
            # Создаем промпт
            prompt = self.create_prompt(message)
            
            # Токенизируем с attention_mask
            inputs = self.tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Генерация с безопасными параметрами
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=inputs.input_ids.shape[1] + 50,  # Короткие ответы
                    num_return_sequences=1,
                    temperature=0.9,  # Более консервативный параметр
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.0,  # Убираем penalty для стабильности
                    top_p=0.95,
                    top_k=40,
                    early_stopping=True
                )
            
            # Декодируем ответ
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем только ответ
            response = self.extract_response(generated_text, prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации: {e}")
            return self.get_fallback_response(message)
    
    def create_prompt(self, message: str) -> str:
        """Создание промпта для генерации"""
        # Более естественный промпт
        return f"Разговор:\nЧеловек: {message}\nAI:"
    
    def extract_response(self, full_text: str, prompt: str) -> str:
        """Извлечение ответа из сгенерированного текста"""
        # Убираем промпт
        response = full_text.replace(prompt, "").strip()
        
        # Очищаем ответ
        response = self.clean_response(response)
        
        return response if response else "Интересно! Расскажи подробнее."
    
    def clean_response(self, text: str) -> str:
        """Очистка сгенерированного текста"""
        import re
        
        # Удаляем лишние префиксы
        patterns = [
            r'^(AI|Ассистент|Бот|Клон|Assistant):\s*',
            r'^(Пользователь|User|Человек):\s*',
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Обрезаем до первого конца предложения
        sentence_end = re.search(r'[.!?…]', cleaned)
        if sentence_end:
            cleaned = cleaned[:sentence_end.end()].strip()
        
        # Удаляем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def get_fallback_response(self, message: str) -> str:
        """Умные запасные ответы"""
        message_lower = message.lower()
        
        # Контекстные ответы
        if any(word in message_lower for word in ['привет', 'здравствуй', 'хай']):
            return "Привет! Рад общению!"
        elif any(word in message_lower for word in ['как дела', 'как ты']):
            return "Всё отлично! А у тебя как?"
        elif any(word in message_lower for word in ['имя', 'зовут']):
            return "Я твой AI-клон! Можешь называть меня как хочешь)"
        elif any(word in message_lower for word in ['игра', 'играть', 'игры']):
            return "Люблю разные игры! А ты во что любишь играть?"
        else:
            fallbacks = [
                "Интересный вопрос! Что думаешь об этом?",
                "Давай поговорим об этом подробнее!",
                "Расскажи больше, мне интересно!",
                "Хорошая тема для разговора!",
            ]
            import random
            return random.choice(fallbacks)

# Инициализация FastAPI
app = FastAPI(
    title="AI Clone Server",
    description="Сервер для общения с AI-клонами",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные экземпляры
clone_manager = CloneManager()
generators_cache = {}

def get_generator(user_id: str) -> CloneGenerator:
    """Получение генератора из кэша или создание нового"""
    if user_id not in generators_cache:
        generators_cache[user_id] = CloneGenerator(user_id)
    return generators_cache[user_id]

# Загрузка HTML шаблонов
def load_html_template(template_name: str) -> str:
    """Загрузка HTML шаблона из файла"""
    try:
        template_path = f"templates/{template_name}"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки шаблона {template_name}: {e}")
        return "<html><body><h1>Ошибка загрузки шаблона</h1></body></html>"

# Роуты API
@app.get("/")
async def root():
    return {
        "message": "AI Clone Server is running!",
        "status": "active",
        "version": "2.0.0"
    }

@app.get("/status")
async def get_status():
    """Статус сервера"""
    active_clones = clone_manager.get_all_clones()
    return {
        "status": "running",
        "active_clones": len(active_clones),
        "total_clones": len(clone_manager.links),
        "loaded_models": len(generators_cache)
    }

@app.post("/clone/register")
async def register_clone(user_id: str, clone_name: str):
    """Регистрация нового клона"""
    try:
        token = clone_manager.register_clone(user_id, clone_name)
        web_url = f"http://localhost:8001/clone/{token}/web"
        
        return {
            "success": True,
            "token": token,
            "web_url": web_url,
            "message": "Клон успешно зарегистрирован"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clone/{token}")
async def get_clone_info(token: str):
    """Информация о клоне"""
    clone_info = clone_manager.get_clone_info(token)
    if not clone_info:
        raise HTTPException(status_code=404, detail="Клон не найден")
    
    return {
        "clone_name": clone_info.get('name', 'Unknown'),
        "user_id": clone_info.get('user_id'),
        "created_at": clone_info.get('created_at'),
        "status": "active",
        "access_count": clone_info.get('access_count', 0)
    }

@app.post("/clone/{token}/chat")
async def chat_with_clone(token: str, request: ChatRequest):
    """Чат с AI-клоном"""
    user_id = clone_manager.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=404, detail="Клон не найден")
    
    try:
        # Получаем генератор для пользователя
        generator = get_generator(user_id)
        
        # Генерируем ответ
        response = generator.generate_response(request.message)
        
        logger.info(f"💬 Чат с клоном {token}: '{request.message}' -> '{response}'")
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в чате: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации ответа")

@app.get("/clone/{token}/web", response_class=HTMLResponse)
async def web_interface(token: str):
    """Веб-интерфейс для чата с клоном"""
    clone_info = clone_manager.get_clone_info(token)
    if not clone_info:
        # Используем шаблон ошибки
        error_html = load_html_template("error.html")
        return HTMLResponse(content=error_html.replace("{{token}}", token))
    
    # Используем шаблон чата
    chat_html = load_html_template("chat.html")
    
    # Заменяем плейсхолдеры
    chat_html = chat_html.replace("{{clone_name}}", clone_info.get('name', 'AI Клон'))
    chat_html = chat_html.replace("{{token}}", token)
    
    # Форматируем дату
    created_at = clone_info.get('created_at', 'Неизвестно')
    try:
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        formatted_date = created_dt.strftime("%d.%m.%Y %H:%M")
    except:
        formatted_date = created_at
    
    chat_html = chat_html.replace("{{created_at}}", formatted_date)
    
    return HTMLResponse(content=chat_html)

@app.get("/clones")
async def list_clones():
    """Список всех активных клонов"""
    active_clones = clone_manager.get_all_clones()
    return {
        "total": len(active_clones),
        "clones": active_clones
    }

@app.delete("/clone/{token}")
async def delete_clone(token: str):
    """Удаление клона"""
    if token in clone_manager.links:
        clone_manager.links[token]['active'] = False
        clone_manager.save_links()
        
        # Удаляем генератор из кэша если есть
        user_id = clone_manager.links[token].get('user_id')
        if user_id in generators_cache:
            del generators_cache[user_id]
        
        return {"success": True, "message": "Клон деактивирован"}
    else:
        raise HTTPException(status_code=404, detail="Клон не найден")

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Запускаем AI Clone Server v2.0...")
    logger.info("📊 Статистика при запуске:")
    
    active_clones = clone_manager.get_all_clones()
    logger.info(f"✅ Активных клонов: {len(active_clones)}")
    
    for token, info in active_clones.items():
        logger.info(f"   - {token}: {info.get('name')} (user: {info.get('user_id')})")
    
    # Создаем папку для шаблонов если её нет
    os.makedirs("templates", exist_ok=True)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")