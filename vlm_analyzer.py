import json
import base64
import os
from openai import AsyncOpenAI
from deep_translator import GoogleTranslator

# Глобальная переменная для хранения переведенных критериев
translated_criteria_text = ""

# Клиент инициализируется после загрузки конфига через init_client()
# Дефолт — локальный LM Studio (на случай если init_client не вызван)
client = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def init_client(base_url: str = "http://localhost:1234/v1", api_key: str = "lm-studio"):
    """
    Инициализирует VLM-клиент с заданными параметрами.
    
    Вызвать из tg_client.py перед запуском воркера:
        from vlm_analyzer import init_client
        init_client(config['VLM_URL'], config['VLM_KEY'])
    Или добавить в .env:
        VLM_URL=https://your-remote-server/v1
        VLM_KEY=your-api-key
    """
    global client
    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    print(f"\033[90m[VLM] Клиент инициализирован: {base_url}\033[0m")

def load_and_translate_criteria(filepath: str = "criteria.txt"):
    """Читает файл с критериями и переводит их на английский один раз при старте."""
    global translated_criteria_text
    
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

def encode_image(image_path: str) -> str:
    """Кодирует локальное изображение в base64 строку для передачи в VLM"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

async def analyze_profile(text: str, image_path: str = None, mode: str = "binary") -> dict:
    """
    Анализирует анкету с помощью VLM модели.
    
    Параметры:
        text: текст анкеты
        image_path: путь к фото анкеты (если есть)
        mode: "binary" — лайк/дизлайк, "score" — оценка 1-10 / skip
    
    Возвращает словарь {"action": ..., "reason": ...}
    """
    # Загружаем свою анкету для контекста VLM
    my_profile = "Анкета не загружена. Оценивай на общих основаниях."
    profile_path = "data/my_profile.json"
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                my_profile = data.get("profile_text", my_profile)
        except Exception:
            pass

    # Выбираем промпт в зависимости от режима бота
    if mode == "score":
        prompt = f"""
You are an advanced profile filtering agent for a dating application. Your task is to analyze the provided screenshot/photo and the accompanying profile text based on strict user preferences.

MY PROFILE (context):
"{my_profile}"

USER PREFERENCES AND CRITERIA (Translated from user config):
{translated_criteria_text}

Analyze the provided profile based STRICTLY on the criteria above.

SCORING RULES:
- "skip": Toxic profile, age under 16, or blatant spam.
- "1" to "5": Uninteresting profile (poor appearance, non-Slavic name, incompatibility).
- "6" to "8": Normal profile, acceptable compatibility.
- "9" to "10": Excellent profile, high compatibility.

RESPONSE FORMAT:
You must respond strictly in JSON format. Do not include any markdown formatting outside the JSON block.
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
        prompt = f"""
You are an advanced profile filtering agent for a dating application. Your task is to analyze the provided screenshot/photo and the accompanying profile text based on strict user preferences.

MY PROFILE (context):
"{my_profile}"

USER PREFERENCES AND CRITERIA (Translated from user config):
{translated_criteria_text}

Analyze the provided profile based STRICTLY on the criteria above.
If the profile satisfies ALL criteria above, output LIKE. Otherwise, output DISLIKE.

RESPONSE FORMAT:
You must respond strictly in JSON format. Do not include any markdown formatting outside the JSON block.
{{
  "action": "like",
  "reason": "Brief, clear explanation of your decision in RUSSIAN language"
}}
Action must be exactly "like" or "dislike".

INCOMING PROFILE:
"{text}"
"""

    # Формируем контент для мультимодальной модели (текст + фото)
    content_list = [{"type": "text", "text": prompt}]

    if image_path and os.path.exists(image_path):
        try:
            base64_image = encode_image(image_path)
            content_list.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        except Exception as e:
            print(f"[-] Не удалось закодировать картинку: {e}")

    content = ""
    try:
        response = await client.chat.completions.create(
            model="qwen3-vl-8b",
            messages=[{"role": "user", "content": content_list}],
            temperature=0.1
        )
        content = response.choices[0].message.content

        # Извлекаем JSON из ответа модели
        json_start = content.find('{')
        json_end = content.rfind('}')
        if json_start != -1 and json_end != -1 and json_end >= json_start:
            json_str = content[json_start:json_end+1]
            return json.loads(json_str)
        else:
            raise ValueError("Не найдены фигурные скобки JSON в ответе модели")
    except Exception as e:
        print(f"[-] Ошибка парсинга или запроса VLM: {e}")
        if content:
            print(f"[-] Сырой ответ модели: {content}")
        # Безопасное значение по умолчанию в зависимости от режима
        default_action = "skip" if mode == "score" else "dislike"
        return {"action": default_action, "reason": "ошибка разбора ответа VLM"}