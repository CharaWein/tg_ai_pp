import subprocess
import sys

def install_requirements():
    """Установка зависимостей"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

if __name__ == "__main__":
    install_requirements()
    print("✅ Все зависимости установлены!")