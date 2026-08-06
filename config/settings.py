import os
import json
import random
from dotenv import load_dotenv

import sys
import colorama

# Устанавливаем универсальный путь для работы в скомпилированном .exe
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENV_PATH = os.path.join(BASE_DIR, ".env")
PHRASES_PATH = os.path.join(BASE_DIR, "data", "phrases.json")

# Инициализация ANSI-цветов для консоли Windows
colorama.init()
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def run_setup_wizard():
    print("\n\033[95m=== 🛠️ МАСТЕР ПЕРВОЙ НАСТРОЙКИ (SETUP WIZARD) ===\033[0m")
    print("\033[90mПривет! Похоже, ты запускаешь бота впервые. Давай всё настроим.\033[0m\n")
    
    api_id = input("\033[96m[1/4] Введите Telegram API_ID:\033[0m ").strip()
    api_hash = input("\033[96m[2/4] Введите Telegram API_HASH:\033[0m ").strip()
    
    default_path = "data/downloads"
    download_dir = input(f"\033[96m[3/4] Папка для фото анкет (Enter = {default_path}):\033[0m ").strip() or default_path
    
    gemini_key = input("\033[96m[4/5] Введите Google Gemini API Key:\033[0m ").strip()
    
    print("\n\033[96m[5/5] Выберите VLM-модель:\033[0m")
    print("  [1] gemini-3.5-flash-lite (500 RPD / 15 RPM) — По умолчанию")
    print("  [2] gemini-3.1-flash-lite (500 RPD / 15 RPM)")
    print("  [3] gemini-2.5-flash (20 RPD / 5 RPM)")
    print("  [4] gemini-3.5-flash (20 RPD / 5 RPM)")
    
    model_choice = input("\033[96mВведите номер (1-4, Enter = 1):\033[0m ").strip()
    
    models_map = {
        "1": "gemini-3.5-flash-lite",
        "2": "gemini-3.1-flash-lite",
        "3": "gemini-2.5-flash",
        "4": "gemini-3.5-flash"
    }
    
    selected_model = models_map.get(model_choice, "gemini-3.5-flash-lite")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(f"API_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")
        f.write(f"DOWNLOAD_DIR={download_dir}\n")
        f.write(f"GEMINI_API_KEY={gemini_key}\n")
        f.write(f"PRIMARY_VLM_MODEL={selected_model}\n")
    print("\n\033[92m[🟢] Отлично! Настройки сохранены в .env\033[0m")

def load_config():
    if not os.path.exists(ENV_PATH):
        try:
            run_setup_wizard()
        except KeyboardInterrupt:
            print("\n\033[91m[!] Настройка прервана. Выход...\033[0m")
            sys.exit(1)
        except Exception as e:
            print(f"\n\033[91m[❌] Ошибка настройки: {e}\033[0m")
            sys.exit(1)

    load_dotenv(ENV_PATH)
    
    api_id_str = os.getenv("API_ID", "").strip()
    if not api_id_str or not api_id_str.isdigit():
        print("\n\033[93m[⚠️] Файл .env пуст или поврежден (API_ID не найден). Запускаем мастер настройки...\033[0m")
        run_setup_wizard()
        load_dotenv(ENV_PATH, override=True)
        api_id_str = os.getenv("API_ID", "").strip()
        
    api_id = int(api_id_str) if api_id_str.isdigit() else 0
    api_hash = os.getenv("API_HASH", "").strip()
    
    # Читаем DOWNLOAD_DIR (или старый DOWNLOAD_PATH для безопасности)
    default_downloads = os.path.join(BASE_DIR, "data", "downloads")
    download_dir = os.getenv("DOWNLOAD_DIR", os.getenv("DOWNLOAD_PATH", default_downloads)).strip()
    if not os.path.isabs(download_dir):
        download_dir = os.path.join(BASE_DIR, download_dir)
    
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_keys_str = os.getenv("GEMINI_API_KEYS", "").strip()
    if not gemini_keys_str and gemini_key:
        gemini_keys_str = gemini_key
    
    primary_vlm_model = os.getenv("PRIMARY_VLM_MODEL", "gemini-3.5-flash-lite").strip()
    
    return {
        "API_ID": api_id,
        "API_HASH": api_hash,
        "DOWNLOAD_DIR": download_dir,
        "DOWNLOAD_PATH": download_dir,
        "HISTORY_PATH": os.path.join(BASE_DIR, "data", "history.md"),
        "PHRASES_PATH": PHRASES_PATH,
        "GEMINI_API_KEY": gemini_key,
        "GEMINI_API_KEYS": gemini_keys_str,
        "PRIMARY_VLM_MODEL": primary_vlm_model,
        "VLM_KEY": gemini_key, # Для обратной совместимости
        "VLM_URL": "", # Для обратной совместимости
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