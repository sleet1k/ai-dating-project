import json
import base64
import os
import asyncio
from google import genai
from google.genai import types
from deep_translator import GoogleTranslator
from config.settings import BASE_DIR

# Глобальная переменная для хранения переведенных критериев
translated_criteria_text = ""

# Кэш для профиля
_my_profile_cache = None

# Глобальный клиент VLM
client = None
api_keys = []
current_key_idx = 0

def init_client(base_url: str = None, api_key: str = None):
    """
    Инициализирует VLM-клиент Google GenAI.
    """
    global client, api_keys, current_key_idx
    keys_str = os.getenv("GEMINI_API_KEYS", "").strip()
    if keys_str:
        api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    else:
        single_key = os.getenv("GEMINI_API_KEY", "").strip()
        api_keys = [single_key] if single_key else []
        
    if not api_keys:
        print("\033[93m[⚠️] GEMINI_API_KEYS не задан в переменных окружения!\033[0m")
        return
        
    client = genai.Client(api_key=api_keys[current_key_idx])
    print(f"\033[90m[VLM] Клиент Google GenAI инициализирован (Ключей: {len(api_keys)})\033[0m")

def get_my_profile() -> str:
    """Загружает анкету пользователя один раз и кэширует ее."""
    global _my_profile_cache
    if _my_profile_cache is not None:
        return _my_profile_cache
        
    _my_profile_cache = "Анкета не загружена. Оценивай на общих основаниях."
    profile_path = os.path.join(BASE_DIR, "data", "my_profile.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _my_profile_cache = data.get("profile_text", _my_profile_cache)
        except Exception:
            pass
    return _my_profile_cache

def load_and_translate_criteria(filepath: str = None):
    """
    Читает criteria.txt (или переданный файл), переводит его на английский и кэширует в памяти.
    """
    global translated_criteria_text
    
    if filepath is None:
        filepath = os.path.join(BASE_DIR, "criteria.txt")
        
    if not os.path.exists(filepath):
        print(f"\033[93m[⚠️] Файл {filepath} не найден, использую пустые критерии.\033[0m")
        translated_criteria_text = "No strict criteria."
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()
            
        if not raw_text:
            translated_criteria_text = "No strict criteria."
            return
            
        print(f"\033[90m[VLM] Перевод пользовательских критериев на английский...\033[0m")
        translated_criteria_text = GoogleTranslator(source='auto', target='en').translate(raw_text)
        print(f"\033[92m[🟢] Критерии успешно переведены и загружены!\033[0m")
    except Exception as e:
        print(f"\033[91m[❌] Ошибка при чтении/переводе {filepath}: {e}\033[0m")
        translated_criteria_text = "No strict criteria due to translation error."

def encode_image(image_path: str) -> types.Part:
    """Кодирует локальное изображение как Part для Gemini"""
    with open(image_path, "rb") as image_file:
        img_bytes = image_file.read()
    # Gemini автоматически определяет тип по mime_type, используем image/jpeg как базовый
    return types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")

async def analyze_profile(text: str, image_path: str = None, mode: str = "binary") -> dict:
    """
    Анализирует анкету с помощью VLM модели.
    
    Параметры:
        text: текст анкеты
        image_path: путь к фото анкеты (если есть)
        mode: "binary" — лайк/дизлайк, "score" — оценка 1-10 / skip
    
    Возвращает словарь {"action": ..., "reason": ...}
    """
    global client, api_keys, current_key_idx
    if client is None:
        init_client()

    my_profile = get_my_profile()
    model_name = os.getenv("PRIMARY_VLM_MODEL", "gemini-3.5-flash-lite")

    system_instruction = f"""Role: Strict dating profile evaluator.
Rules: Evaluate target photo and bio based on user criteria and my_profile context.
Output: Response MUST be a valid JSON object matching the requested schema. Reason MUST be concise (under 15 words).

MY PROFILE (context):
"{my_profile}"

USER PREFERENCES AND CRITERIA (Translated from user config):
{translated_criteria_text}"""

    # Выбираем промпт в зависимости от режима бота
    if mode == "score":
        prompt = f"""Analyze the provided profile based STRICTLY on the criteria above.

SCORING RULES:
- "skip": Toxic profile, age under 16, or blatant spam.
- "1" to "5": Uninteresting profile (poor appearance, non-Slavic name, incompatibility).
- "6" to "8": Normal profile, acceptable compatibility.
- "9" to "10": Excellent profile, high compatibility.

SCHEMA:
{{
  "action": "7", 
  "reason": "Brief, clear explanation of your decision in RUSSIAN language"
}}
Examples of action: "skip", "1", "3", "6", "8", "10"

INCOMING PROFILE:
"{text}"
"""
    else:
        # Режим binary — классический лайк/дизлайк
        prompt = f"""Analyze the provided profile based STRICTLY on the criteria above.
If the profile satisfies ALL criteria above, output LIKE. Otherwise, output DISLIKE.

SCHEMA:
{{
  "action": "like",
  "reason": "Brief, clear explanation of your decision in RUSSIAN language"
}}
Action must be exactly "like" or "dislike".

INCOMING PROFILE:
"{text}"
"""

    contents = [prompt]

    if image_path and os.path.exists(image_path):
        try:
            image_part = encode_image(image_path)
            contents.insert(0, image_part)
        except Exception as e:
            print(f"[-] Не удалось загрузить картинку: {e}")

    # global moved to start of function
    
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            content = response.text
            return json.loads(content)
        except genai.errors.APIError as e:
            if e.code == 429 or "429" in str(e):
                if len(api_keys) > 1:
                    masked_key = api_keys[current_key_idx][:8] + "..."
                    print(f"\n\033[93m[⚠️] Ключ {masked_key} исчерпан (429), переключаюсь на следующий...\033[0m")
                    current_key_idx = (current_key_idx + 1) % len(api_keys)
                    client = genai.Client(api_key=api_keys[current_key_idx])
                    attempt -= 1 # Не считаем смену ключа за попытку
                    continue
                else:
                    print(f"[-] Ошибка 429 (Лимит исчерпан). Пауза 5 сек...")
                    await asyncio.sleep(5)
                    continue
            elif e.code in [503, 500, 502, 504] or any(str(c) in str(e) for c in [503, 500, 502, 504]):
                delay = 2 ** attempt
                print(f"\033[93m[-] Ошибка сервера Gemini ({getattr(e, 'code', 'unknown')}). Попытка {attempt}/{max_attempts} через {delay} сек...\033[0m")
                await asyncio.sleep(delay)
                continue
            else:
                print(f"[-] Ошибка запроса VLM: {e}")
                break
        except Exception as e:
            delay = 2 ** attempt
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                print(f"\033[93m[-] Таймаут сети. Попытка {attempt}/{max_attempts} через {delay} сек...\033[0m")
                await asyncio.sleep(delay)
                continue
            print(f"[-] Ошибка парсинга или запроса VLM: {e}")
            break

    default_action = "skip" if mode == "score" else "dislike"
    return {"action": default_action, "reason": "ошибка после всех попыток запроса VLM"}