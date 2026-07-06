import os
import json
import random
from dotenv import load_dotenv

ENV_PATH = ".env"
PHRASES_PATH = "data/phrases.json"

def load_config():
    if not os.path.exists(ENV_PATH):
        print("\n\033[95m=== 🛠️ МАСТЕР ПЕРВОЙ НАСТРОЙКИ (SETUP WIZARD) ===\033[0m")
        print("\033[90mПривет! Похоже, ты запускаешь бота впервые. Давай всё настроим.\033[0m\n")
        
        api_id = input("\033[96m[1/3] Введите Telegram API_ID:\033[0m ").strip()
        api_hash = input("\033[96m[2/3] Введите Telegram API_HASH:\033[0m ").strip()
        
        default_path = "data/downloads"
        download_path = input(f"\033[96m[3/3] Папка для фото анкет (Enter = {default_path}):\033[0m ").strip()
        if not download_path:
            download_path = default_path
            
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"API_ID={api_id}\nAPI_HASH={api_hash}\nDOWNLOAD_PATH={download_path}\n")
        print("\n\033[92m[🟢] Отлично! Настройки сохранены в .env\033[0m")

    load_dotenv(ENV_PATH)
    
    return {
        "API_ID": int(os.getenv("API_ID").strip()),
        "API_HASH": os.getenv("API_HASH").strip(),
        "DOWNLOAD_PATH": os.getenv("DOWNLOAD_PATH", "data/downloads").strip(),
        "HISTORY_PATH": "data/history.md",
        "PHRASES_PATH": PHRASES_PATH,
        # VLM настройки: дефолт — локальный LM Studio
        "VLM_URL": os.getenv("VLM_URL", "http://localhost:1234/v1").strip(),
        "VLM_KEY": os.getenv("VLM_KEY", "lm-studio").strip(),
    }

def get_random_phrase(category):
    """Достает случайную фразу из JSON для оживления CLI"""
    if not os.path.exists(PHRASES_PATH):
        default = {
            "thinking": ["Думаю..."], 
            "dislike_comment": ["Мимо"], 
            "like_comment": ["Лайк"]
        }
        return random.choice(default.get(category, ["..."]))
    
    with open(PHRASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return random.choice(data.get(category, ["..."]))