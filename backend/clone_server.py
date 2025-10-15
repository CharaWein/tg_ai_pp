import os
import json
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import uuid
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Clone Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class CloneModel:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        
    def load_user_model(self, user_id: str) -> bool:
        """Загрузка модели для конкретного пользователя"""
        try:
            model_path = f"trained_models/user_{user_id}"
            
            if not os.path.exists(model_path):
                logger.warning(f"Модель для пользователя {user_id} не найдена")
                return False
            
            if user_id in self.models:
                logger.info(f"Модель для пользователя {user_id} уже загружена")
                return True
            
            logger.info(f"Загружаем модель для пользователя {user_id}")
            self.tokenizers[user_id] = AutoTokenizer.from_pretrained(model_path)
            self.models[user_id] = AutoModelForCausalLM.from_pretrained(model_path)
            
            if self.tokenizers[user_id].pad_token is None:
                self.tokenizers[user_id].pad_token = self.tokenizers[user_id].eos_token
            
            logger.info(f"✅ Модель для пользователя {user_id} успешно загружена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели для {user_id}: {e}")
            return False
    
    def generate_response(self, user_id: str, message: str) -> str:
        """Генерация ответов"""
        try:
            if user_id not in self.models:
                if not self.load_user_model(user_id):
                    return "Привет! Рад общению!"
            
            tokenizer = self.tokenizers[user_id]
            model = self.models[user_id]
            
            # Простой промпт
            prompt = f"Человек: {message}\nAI:"
            
            inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=128, truncation=True)
            
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_length=len(inputs[0]) + 50,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    top_p=0.9,
                    early_stopping=True
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "AI:" in response:
                response = response.split("AI:")[-1].strip()
            else:
                response = response.replace(prompt, "").strip()
            
            if not response:
                response = "Интересно! Расскажи подробнее."
            
            return response
                
        except Exception as e:
            logger.error(f"Ошибка генерации для {user_id}: {e}")
            return "Давайте поговорим о чем-нибудь!"

class SimpleShareService:
    def __init__(self):
        self.links_file = "clone_links.json"
        self.links = self.load_links()
    
    def load_links(self):
        """Загрузка ссылок из файла"""
        try:
            if os.path.exists(self.links_file):
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    links = json.load(f)
                    logger.info(f"✅ Загружено {len(links)} токенов из файла")
                    return links
            else:
                logger.info("Файл ссылок не найден, создаем новый")
                links = {}
                self.save_links(links)
                return links
        except Exception as e:
            logger.error(f"Ошибка загрузки ссылок: {e}")
            return {}
    
    def save_links(self, links=None):
        """Сохранение ссылок в файл"""
        try:
            if links is None:
                links = self.links
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)
            logger.info("✅ Ссылки сохранены в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения ссылок: {e}")
    
    def generate_share_link(self, user_id: str, clone_name: str) -> str:
        """Генерация ссылки для доступа к клону"""
        try:
            logger.info(f"🔗 Генерация ссылки для user_id: {user_id}, clone_name: {clone_name}")
            
            # Сначала деактивируем старые ссылки для этого пользователя
            deactivated_count = 0
            for token, info in list(self.links.items()):
                if info.get('user_id') == user_id and info.get('active', True):
                    info['active'] = False
                    deactivated_count += 1
            
            if deactivated_count > 0:
                logger.info(f"🗑️ Деактивировано {deactivated_count} старых ссылок")
            
            # Создаем новую ссылку
            token = str(uuid.uuid4())
            
            self.links[token] = {
                'user_id': user_id,
                'name': clone_name,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
            self.save_links()
            
            logger.info(f"✅ Сгенерирован токен для {user_id}: {token}")
            
            return token
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ссылки: {e}")
            return str(uuid.uuid4())
    
    def get_user_id_by_token(self, token: str):
        """Получение user_id по токену"""
        logger.info(f"🔍 Поиск user_id для токена: {token}")
        
        if token in self.links:
            link_info = self.links[token]
            is_active = link_info.get('active', True)
            user_id = link_info.get('user_id')
            
            logger.info(f"📋 Найден токен: active={is_active}, user_id={user_id}")
            
            if is_active:
                return user_id
            else:
                logger.warning(f"❌ Токен {token} неактивен")
        else:
            logger.warning(f"❌ Токен {token} не найден в базе")
        
        return None
    
    def get_all_links(self):
        """Получение всех активных ссылок"""
        active_links = {}
        for token, info in self.links.items():
            if info.get('active', True):
                active_links[token] = info
        
        logger.info(f"📊 Активных ссылок: {len(active_links)}")
        return active_links

    def get_user_links(self, user_id: str):
        """Получение всех ссылок пользователя"""
        user_links = {}
        for token, info in self.links.items():
            if info.get('user_id') == user_id:
                user_links[token] = info
        
        logger.info(f"👤 Пользователь {user_id} имеет {len(user_links)} ссылок")
        return user_links

# Инициализация сервисов
clone_model = CloneModel()
share_service = SimpleShareService()

@app.get("/")
async def root():
    return {"message": "AI Clone Server is running!", "status": "active"}

@app.get("/status")
async def status():
    active_models = len(clone_model.models)
    active_links = len(share_service.get_all_links())
    return {
        "status": "running",
        "active_models": active_models,
        "active_links": active_links,
        "total_tokens": len(share_service.links)
    }

@app.get("/debug/links")
async def debug_links():
    """Отладочная информация о ссылках"""
    return {
        "all_links": share_service.links,
        "active_links": share_service.get_all_links()
    }

@app.get("/clone/{token}")
async def get_clone_info(token: str):
    """Информация о клоне"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    clone_info = share_service.links.get(token, {})
    return {
        "clone_name": clone_info.get('name', 'Unknown'),
        "user_id": user_id,
        "created_at": clone_info.get('created_at'),
        "status": "active"
    }

@app.post("/clone/{token}/chat")
async def chat_with_clone(token: str, request: ChatRequest):
    """Чат с AI-клоном"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        raise HTTPException(status_code=404, detail="Clone not found")
    
    try:
        response = clone_model.generate_response(user_id, request.message)
        return ChatResponse(response=response)
    
    except Exception as e:
        logger.error(f"Ошибка в чате с клоном {token}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/clone/{token}/web", response_class=HTMLResponse)
async def clone_web_interface(token: str):
    """Веб-интерфейс для чата с клоном"""
    user_id = share_service.get_user_id_by_token(token)
    if not user_id:
        # ИСПРАВЛЕННАЯ ЧАСТЬ - убрано неправильное форматирование
        html_content = """
        <html>
            <head>
                <title>Клон не найден</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        max-width: 800px; 
                        margin: 0 auto; 
                        padding: 40px; 
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container {
                        background: white;
                        border-radius: 15px;
                        padding: 40px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    }
                    h1 { color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Клон не найден</h1>
                    <p>Ссылка недействительна или клон был удален.</p>
                    <p><small>Токен: """ + token + """</small></p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    
    clone_info = share_service.links.get(token, {})
    clone_name = clone_info.get('name', 'AI Клон')
    created_at = clone_info.get('created_at', 'Неизвестно')
    
    # Форматируем дату
    try:
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        formatted_date = created_dt.strftime("%d.%m.%Y %H:%M")
    except:
        formatted_date = created_at
    
    html_content = f"""
    <html>
        <head>
            <title>{clone_name} - AI Клон</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 20px;
                }}
                .chat-container {{ 
                    border: 2px solid #e0e0e0; 
                    padding: 20px; 
                    height: 400px; 
                    overflow-y: scroll; 
                    margin-bottom: 20px;
                    border-radius: 10px;
                    background: #fafafa;
                }}
                .message {{ 
                    margin: 15px 0; 
                    padding: 12px 16px; 
                    border-radius: 15px;
                    max-width: 80%;
                    word-wrap: break-word;
                }}
                .user {{ 
                    background: #007bff; 
                    color: white;
                    margin-left: auto;
                    margin-right: 0;
                }}
                .bot {{ 
                    background: #f1f3f4; 
                    color: #333;
                    margin-left: 0;
                    margin-right: auto;
                }}
                .input-group {{
                    display: flex;
                    gap: 10px;
                }}
                input {{ 
                    flex: 1; 
                    padding: 12px; 
                    border: 2px solid #ddd;
                    border-radius: 25px;
                    font-size: 16px;
                }}
                input:focus {{
                    outline: none;
                    border-color: #007bff;
                }}
                button {{ 
                    padding: 12px 25px; 
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    cursor: pointer;
                    border-radius: 25px;
                    font-size: 16px;
                    transition: background 0.3s;
                }}
                button:hover {{
                    background: #0056b3;
                }}
                .info {{
                    background: #e7f3ff;
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    border-left: 4px solid #007bff;
                }}
                .token-info {{
                    background: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    font-size: 12px;
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 {clone_name}</h1>
                    <p>AI клон обучен на стиле общения пользователя</p>
                    <div class="info">
                        <strong>ℹ️ Информация:</strong><br>
                        • Создан: {formatted_date}<br>
                        • Модель: Russian GPT-2 с дообучением<br>
                        • Просто начните диалог ниже!
                        <div class="token-info">Токен: {token}</div>
                    </div>
                </div>
                
                <div id="chat" class="chat-container"></div>
                
                <div class="input-group">
                    <input type="text" id="message" placeholder="Введите ваше сообщение..." onkeypress="handleKeyPress(event)">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
            </div>
            
            <script>
                const chat = document.getElementById('chat');
                const messageInput = document.getElementById('message');
                
                function addMessage(text, isUser) {{
                    const messageDiv = document.createElement('div');
                    messageDiv.className = isUser ? 'message user' : 'message bot';
                    messageDiv.textContent = text;
                    chat.appendChild(messageDiv);
                    chat.scrollTop = chat.scrollHeight;
                }}
                
                function handleKeyPress(event) {{
                    if (event.key === 'Enter') {{
                        sendMessage();
                    }}
                }}
                
                async function sendMessage() {{
                    const message = messageInput.value.trim();
                    if (!message) return;
                    
                    addMessage(message, true);
                    messageInput.value = '';
                    messageInput.disabled = true;
                    
                    try {{
                        const response = await fetch('/clone/{token}/chat', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ message: message }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error('Ошибка сервера');
                        }}
                        
                        const data = await response.json();
                        addMessage(data.response, false);
                    }} catch (error) {{
                        addMessage('❌ Ошибка соединения с сервером', false);
                    }} finally {{
                        messageInput.disabled = false;
                        messageInput.focus();
                    }}
                }}
                
                // Приветственное сообщение
                addMessage('Привет! Я ваш AI-клон, обученный на вашем стиле общения. Давайте пообщаемся!', false);
                
                // Фокус на поле ввода
                messageInput.focus();
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/user/{user_id}/links")
async def get_user_links(user_id: str):
    """Получить все ссылки пользователя"""
    user_links = share_service.get_user_links(user_id)
    return {
        "user_id": user_id,
        "links": user_links,
        "total": len(user_links)
    }

@app.delete("/clone/{token}")
async def delete_clone_link(token: str):
    """Удалить ссылку на клона"""
    if token in share_service.links:
        share_service.links[token]['active'] = False
        share_service.save_links()
        return {"status": "deleted", "token": token}
    else:
        raise HTTPException(status_code=404, detail="Token not found")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Запускаем AI Clone Server...")
    logger.info("📊 Статус ссылок при запуске:")
    
    # Проверяем ссылки при запуске
    active_links = share_service.get_all_links()
    logger.info(f"✅ Активных ссылок: {len(active_links)}")
    
    for token, info in active_links.items():
        logger.info(f"   - {token}: {info.get('name')} (user: {info.get('user_id')})")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)