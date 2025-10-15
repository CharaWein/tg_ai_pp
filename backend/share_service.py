import secrets
import json
import os
from datetime import datetime, timedelta

class CloneShareService:
    def __init__(self):
        self.links_file = "clone_links.json"
        self.links = {}
        self.load_links()
        print(f"✅ ShareService инициализирован. Загружено {len(self.links)} токенов")
    
    def load_links(self):
        """Загрузка существующих ссылок"""
        if os.path.exists(self.links_file):
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    self.links = json.load(f)
                print(f"✅ Загружено {len(self.links)} токенов из {self.links_file}")
            except Exception as e:
                print(f"❌ Ошибка загрузки links: {e}")
                self.links = {}
        else:
            print(f"ℹ️ Файл {self.links_file} не найден, создаём новый")
            self.links = {}
    
    def save_links(self):
        """Сохранение ссылок"""
        try:
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(self.links, f, ensure_ascii=False, indent=2)
            print(f"💾 Ссылки сохранены в {self.links_file}")
        except Exception as e:
            print(f"❌ Ошибка сохранения links: {e}")
    
    def generate_share_link(self, user_id: str, clone_name: str, expires_hours: int = 168):
        """Генерация уникальной ссылки для клона"""
        # Создаём уникальный токен
        token = secrets.token_urlsafe(16)
        
        # Сохраняем информацию о ссылке
        self.links[token] = {
            'user_id': user_id,
            'clone_name': clone_name,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=expires_hours)).isoformat(),
            'access_count': 0
        }
        
        self.save_links()
        
        # Генерируем ссылку (в реальном проекте это будет ваш домен)
        share_url = f"http://localhost:8001/clone/{token}"
        
        print(f"✅ Создана ссылка для {clone_name}: {token}")
        
        return share_url
    
    def get_clone_info(self, token: str):
        """Получение информации о клоне по токену"""
        if token in self.links:
            link_info = self.links[token]
            
            # Проверяем не истекла ли ссылка
            try:
                expires_at = datetime.fromisoformat(link_info['expires_at'])
                if datetime.now() > expires_at:
                    del self.links[token]
                    self.save_links()
                    print(f"🗑️ Токен {token} удалён (истёк)")
                    return None
            except Exception as e:
                print(f"⚠️ Ошибка проверки срока токена {token}: {e}")
            
            # Увеличиваем счётчик использований
            link_info['access_count'] = link_info.get('access_count', 0) + 1
            self.save_links()
            
            print(f"🔍 Найден токен {token} для {link_info['clone_name']}")
            return link_info
        
        print(f"❌ Токен {token} не найден")
        return None

# Создаём глобальный экземпляр
share_service = CloneShareService()