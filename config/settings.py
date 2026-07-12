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
        
        api_id = input("\033[96m[1/5] Введите Telegram API_ID:\033[0m ").strip()
        api_hash = input("\033[96m[2/5] Введите Telegram API_HASH:\033[0m ").strip()
        
        default_path = "data/downloads"
        download_path = input(f"\033[96m[3/5] Папка для фото анкет (Enter = {default_path}):\033[0m ").strip() or default_path
        
        default_vlm_url = "http://localhost:1234/v1"
        vlm_url = input(f"\033[96m[4/5] VLM API URL (Enter = {default_vlm_url}):\033[0m ").strip() or default_vlm_url
        
        default_vlm_key = "lm-studio"
        vlm_key = input(f"\033[96m[5/5] VLM API KEY (Enter = {default_vlm_key}):\033[0m ").strip() or default_vlm_key
            
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"API_ID={api_id}\nAPI_HASH={api_hash}\nDOWNLOAD_PATH={download_path}\n")
            f.write(f"VLM_URL={vlm_url}\nVLM_KEY={vlm_key}\n")
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

def interactive_criteria_wizard(filepath="criteria.txt"):
    print("\n\033[95m=== ⚙️ МАСТЕР НАСТРОЙКИ КРИТЕРИЕВ ИИ ===\033[0m")
    print("\033[90mДавай настроим, кого именно будет искать ИИ. Нажимай Enter, чтобы оставить по умолчанию.\033[0m\n")
    
    age = input("\033[96m[1/4] Желаемый возраст (например, от 18 до 25):\033[0m ").strip()
    looks = input("\033[96m[2/4] Внешность/Типаж (Enter, чтобы пропустить):\033[0m ").strip()
    flags = input("\033[96m[3/4] Красные флаги / Что сразу скипаем (через запятую):\033[0m ").strip()
    interests = input("\033[96m[4/4] Интересы / Плюсы (например: видеоигры, спорт):\033[0m ").strip()

    # Фоллбэк на дефолтные правила, если ничего не ввели
    if not any([age, looks, flags, interests]):
        content = (
            "Возраст: строго от 18 до 25 лет.\n"
            "Внешность: опрятный вид, предпочтительно брюнетки.\n"
            "Красные флаги (сразу SKIP): агрессия, ссылки на инсту/тг в описании, эскорт, поиск спонсора/кошелька, пустые анкеты.\n"
            "Интересы: плюсом будет, если любит видеоигры, мемы или аниме.\n"
        )
    else:
        content = ""
        if age: content += f"Возраст: {age}\n"
        if looks: content += f"Внешность: {looks}\n"
        if flags: content += f"Красные флаги (сразу SKIP): {flags}\n"
        if interests: content += f"Интересы: плюсом будет {interests}\n"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"\n\033[92m[🟢] Критерии успешно сохранены в файл: {filepath}\033[0m")
    except Exception as e:
        print(f"\n\033[91m[❌] Ошибка сохранения критериев: {e}\033[0m")