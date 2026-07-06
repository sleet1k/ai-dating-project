import asyncio
import os
import sys
import random
import datetime
import json
import msvcrt
from telethon import TelegramClient, events
from engines import get_engine

from config.settings import load_config, get_random_phrase
from vlm_analyzer import init_client

# Загружаем конфигурацию из .env (или запускаем Setup Wizard если .env нет)
config = load_config()

# Инициализируем VLM-клиент с параметрами из конфига (.env)
# Чтобы использовать удалённый API, добавь в .env: VLM_URL=... и VLM_KEY=...
init_client(config["VLM_URL"], config["VLM_KEY"])

# ───────────────────────────────────────────────
# Настройки сервисов и скоростей
# ───────────────────────────────────────────────

SERVICES = {
    "1": {"name": "Дайвинчик",  "bot": "leomatchbot"},
    "2": {"name": "Бибинто",    "bot": "bibinto_bot"},
    "3": {"name": "Blurrr",     "bot": "blurrr_dating_bot"},
}

SPEED_MODES = {
    "1": {"name": "Стелс (5-15с)",  "delay": (5, 15)},
    "2": {"name": "Нормал (3-7с)",  "delay": (3, 7)},
    "3": {"name": "Турбо (1-2с)",   "delay": (1, 2)},
}

# Очередь для защиты от нахлёста анкет (обрабатываем строго по одной)
profile_queue: asyncio.Queue = asyncio.Queue()


# ───────────────────────────────────────────────
# Запись истории
# ───────────────────────────────────────────────

def write_history_log(
    service_name: str,
    action: str,
    reason: str,
    profile_text: str,
    photo_path: str,
    tg_message_raw: str,
    script_response: str,
    terminal_log: str,
    error_log: str = ""
):
    """
    Записывает подробный лог обработанной анкеты в data/history.md.
    
    Поля лога:
        service_name    — название сервиса (Дайвинчик, Бибинто, Blurrr)
        action          — вердикт (like / dislike / skip / 1-10)
        reason          — причина от VLM
        profile_text    — текст анкеты из телеграма
        photo_path      — путь к скачанному фото
        tg_message_raw  — полный текст сообщения пришедшего из TG
        script_response — что именно скрипт отправил обратно в чат бота
        terminal_log    — строки вывода терминала для этой анкеты
        error_log       — ошибки выполнения скрипта, если есть
    """
    # Используем абсолютный путь относительно папки скрипта, чтобы не зависеть от cwd
    script_dir = os.path.dirname(os.path.abspath(__file__))
    history_file = os.path.join(script_dir, "data", "history.md")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Эмодзи-вердикт для быстрого визуального сканирования
    if action == "like":
        verdict_emoji = "🟢 ЛАЙК"
    elif action == "skip":
        verdict_emoji = "⏭️ ПРОПУСК"
    elif action.isdigit():
        score = int(action)
        verdict_emoji = f"⭐ ОЦЕНКА {action}/10 {'🔥' if score >= 7 else '👎' if score <= 4 else '😐'}"
    else:
        verdict_emoji = f"🔴 ДИЗЛАЙК ({action})"

    # Цитируем текст анкеты в формате markdown
    quoted_profile = "\n> ".join(profile_text.splitlines()) if profile_text else "*текст отсутствует*"
    quoted_tg_raw  = "\n> ".join(tg_message_raw.splitlines()) if tg_message_raw else "*пусто*"

    block = []
    block.append(f"---")
    block.append(f"### 🕒 {timestamp}  |  📱 {service_name}")
    block.append(f"- **Вердикт**: {verdict_emoji}")
    block.append(f"- **Причина VLM**: {reason}")
    block.append(f"- **Ответ скрипта в чат**: `{script_response}`")

    if photo_path and os.path.exists(photo_path):
        abs_photo = os.path.abspath(photo_path).replace("\\", "/")
        block.append(f"- **Фото анкеты**: [открыть]({abs_photo})")

    if error_log:
        block.append(f"\n#### ❌ ОШИБКА ВЫПОЛНЕНИЯ:\n```\n{error_log}\n```")

    block.append(f"\n#### 📥 Сообщение из Telegram (raw):\n> {quoted_tg_raw}")
    block.append(f"\n#### 👤 Текст анкеты (распознан):\n> {quoted_profile}")

    if terminal_log.strip():
        block.append(f"\n#### 🖥 Лог терминала:\n```\n{terminal_log.strip()}\n```")

    block.append("")  # Пустая строка между записями

    log_text = "\n".join(block) + "\n"

    try:
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(log_text)
    except Exception as e:
        # Выводим в консоль но не падаем
        print(f"\033[91m[❌] ОШИБКА ЗАПИСИ ИСТОРИИ: {e}\033[0m")
        print(f"\033[91m    Путь: {history_file}\033[0m")


# ───────────────────────────────────────────────
# Отображение меню
# ───────────────────────────────────────────────

def show_anime_menu():
    """Отображает главное меню скрипта с анимешным котиком"""
    os.system('cls' if os.name == 'nt' else 'clear')
    menu = """
\033[91m       /\\_/\\  
      ( •.• )    \033[95m █▀█ █▀▄ █▀█ 
      ══█ █══    \033[95m █▀█ █▄▀ █▀▀ \033[90mby sleet1k\033[91m
     (___★___)
  ─────────────────────────────────────────────────────
  \033[96m💡 Нашел жену? Поблагодари автора:\033[0m \033[94mTG: @sleet1k | GitHub: sleet1k\033[0m
  ─────────────────────────────────────────────────────
  \033[95m▸ 1.\033[0m Инициализировать VLM-анализ (Тест-режим)
  \033[95m▸ 2.\033[0m Запустить конвейер дейтинга (Боевой авто-режим)
  \033[95m▸ 3.\033[0m Статус / Тест записи истории
  \033[95m▸ 4.\033[0m Сбросить настройки (.env)
  \033[95m▸ 5.\033[0m Выйти из терминала
  \033[91m─────────────────────────────────────────────────────\033[0m
"""
    print(menu)


# ───────────────────────────────────────────────
# Авто-запрос своей анкеты (отдельная сессия, ДО старта воркера)
# ───────────────────────────────────────────────

async def fetch_and_save_my_profile(engine):
    """
    Запрашивает текст своей анкеты у активного сервиса в ОТДЕЛЬНОЙ короткой сессии.
    Вызывается ДО запуска основного воркера, чтобы не засорять очередь событий.
    Результат сохраняется в data/my_profile.json.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(script_dir, "data", "my_profile.json")

    print(f"\033[90m[*] Автозапрос своей анкеты у @{engine.target_bot}...\033[0m")
    try:
        # Открываем отдельную короткую сессию специально для запроса профиля
        client_tmp = TelegramClient(
            os.path.join(script_dir, "data", "ai_agent_session"),
            api_id=config["API_ID"],
            api_hash=config["API_HASH"]
        )
        async with client_tmp:
            profile_text = await engine.fetch_profile(client_tmp)

        if profile_text:
            os.makedirs(os.path.dirname(profile_path), exist_ok=True)
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump({"profile_text": profile_text}, f, ensure_ascii=False, indent=4)
            preview = profile_text[:80].replace("\n", " ")
            print(f"\033[92m[🟢] Профиль обновлён: {preview}...\033[0m")
        else:
            print(f"\033[93m[⚠️] Не удалось получить анкету от @{engine.target_bot}. Используется предыдущая.\033[0m")
    except Exception as e:
        print(f"\033[91m[-] Ошибка автозапроса профиля: {e}\033[0m")


# ───────────────────────────────────────────────
# Фоновый воркер обработки очереди анкет
# ───────────────────────────────────────────────

async def queue_worker(client, bot_entity, is_test: bool, delay_range: tuple, engine, service_name: str):
    """
    Фоновый воркер: читает анкеты из profile_queue строго по одной,
    отдаёт в VLM и реагирует через движок текущего сервиса.
    """
    from vlm_analyzer import analyze_profile
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = config.get("DOWNLOAD_PATH", os.path.join(script_dir, "data", "downloads"))
    os.makedirs(download_dir, exist_ok=True)

    while True:
        event = await profile_queue.get()
        
        # 1. Сразу отсекаем системный мусор (статусы поиска, анимации, явную рекламу), 
        # чтобы вообще не пускать их в воркер и не засорять логи.
        tg_raw_text_check = getattr(event.message, 'message', "") or ""
        if tg_raw_text_check.strip() in ["✨🔍", "🐨"] or "Ad" in tg_raw_text_check or "Меню:" in tg_raw_text_check:
            profile_queue.task_done()
            continue

        terminal_lines = []  # Буфер строк терминала для этой анкеты
        
        # Дефолтные значения лога на случай падения до их инициализации
        action = "none"
        reason = "Не проверялась"
        profile_text = ""
        photo_path = ""
        tg_raw_text = ""
        script_response = "нет ответа"
        error_log = ""

        def tlog(msg: str):
            """Вспомогательная функция: печатает и сохраняет строку для истории"""
            print(msg)
            # Убираем ANSI-коды для чистого лога
            clean = msg
            for code in ["\033[0m", "\033[90m", "\033[91m", "\033[92m", "\033[93m",
                         "\033[94m", "\033[95m", "\033[96m", "\033[97m"]:
                clean = clean.replace(code, "")
            terminal_lines.append(clean)

        try:
            tg_raw_text = getattr(event.message, 'message', "") or ""

            # Стриппинг системного футера Бибинто (все что после "——" — мусор бота)
            if "——" in tg_raw_text:
                profile_text = tg_raw_text.split("——")[0].strip()
            else:
                profile_text = tg_raw_text.strip()

            profile_text_log = profile_text.replace('\n', ' ')

            phrase = get_random_phrase("thinking")
            tlog(f"\n\033[94m[🧠] {phrase}\033[0m")
            tlog(f"\033[90m[Текст анкеты]:\033[0m {profile_text_log}")

            # Скачиваем фото анкеты (с уникальным именем по ID сообщения)
            if event.message.photo:
                tlog(f"\033[90m[*] Скачиваю фотографию в {download_dir}...\033[0m")
                await asyncio.sleep(0.5)  # Микропауза для обхода ошибки 400
                photo_path = await event.message.download_media(
                    file=os.path.join(download_dir, f"profile_{event.message.id}.jpg")
                )

            # Отдаём анкету в VLM с режимом текущего сервиса
            tlog("\033[95m[*] Ожидаю вердикт от VLM модели в LM Studio...\033[0m")
            default_action = "skip" if engine.vlm_mode == "score" else "dislike"
            try:
                result = await analyze_profile(profile_text, photo_path, mode=engine.vlm_mode)
                action = result.get("action", default_action)
                reason = result.get("reason", "Причина не указана")
            except Exception as vlm_err:
                tlog(f"\033[91m[-] Ошибка API LM Studio: {vlm_err}\033[0m")
                action = default_action
                reason = f"Ошибка запроса к локальной модели: {vlm_err}"
                error_log += f"VLM Error: {vlm_err}\n"

            # Выводим вердикт в консоль
            if engine.vlm_mode == "score":
                if action == "skip":
                    comment = get_random_phrase("dislike_comment")
                    tlog(f"\033[91m[- ПРОПУСК] ({comment}): {reason}\033[0m")
                else:
                    try:
                        score_int = int(action)
                    except (ValueError, TypeError):
                        score_int = 0
                    if score_int >= 6:
                        comment = get_random_phrase("like_comment")
                        tlog(f"\033[93m[⭐ ОЦЕНКА {action}/10] ({comment}): {reason}\033[0m")
                    else:
                        comment = get_random_phrase("dislike_comment")
                        tlog(f"\033[91m[📉 НИЗКИЙ БАЛЛ {action}/10] ({comment}): {reason}\033[0m")
            else:
                if action == "like":
                    comment = get_random_phrase("like_comment")
                    tlog(f"\033[92m[+ ЛАЙК] ({comment}): {reason}\033[0m")
                else:
                    comment = get_random_phrase("dislike_comment")
                    tlog(f"\033[91m[- ДИЗЛАЙК] ({comment}): {reason}\033[0m")

            # Пауза для имитации поведения человека (обход антифрода)
            delay = random.randint(*delay_range)
            tlog(f"\033[90m[*] Пауза {delay} сек...\033[0m")
            await asyncio.sleep(delay)

            # ── Отправка реакции в чат ──
            script_response = "(тест-режим, реакция не отправлена)"

            if is_test:
                tlog("\033[93m[⚠️] Режим ТЕСТ: отправка реакций заблокирована.\033[0m")
            else:
                try:
                    # Получаем свежее сообщение для передачи в движок
                    fresh_msg = await client.get_messages(bot_entity, ids=event.message.id)
                    
                    # Движок сам разберется, слать текст (1/3 или 6/10) или кликать inline-кнопки
                    await engine.click_action(fresh_msg, action)
                    
                    script_response = f'engine_action: "{action}"'
                    # Расчёт отображаемой отправленной оценки для score-режима (для лога)
                    if engine.vlm_mode == "score":
                        if action in ["dislike", "skip"]:
                            sent_val = "3"
                        elif action == "like":
                            sent_val = "8"
                        else:
                            try:
                                s = int(action)
                                sent_val = "3" if s <= 5 else "7" if s <= 7 else "8" if s == 8 else "9"
                            except (ValueError, TypeError):
                                sent_val = "3"
                        tlog(f"\033[{'92' if sent_val in ['7','8','9'] else '91'}m[{'🟢' if sent_val in ['7','8','9'] else '🔴'}] Действие выполнено: {action} (отправлено {sent_val})\033[0m")
                    else:
                        tlog(f"\033[{'92' if action == 'like' else '91'}m[{'🟢' if action == 'like' else '🔴'}] Действие выполнено: {action}\033[0m")
                
                except Exception as btn_err:
                    # Универсальный текстовый фолбэк на случай полной жопы
                    fb_msg = "1" if action in ["like", "10"] else "3" if engine.vlm_mode != "score" else "6"
                    try:
                        await client.send_message(bot_entity, fb_msg)
                        script_response = f'send_message fallback after error: "{fb_msg}"'
                    except Exception as fb_err:
                        script_response = f"ошибка фолбэк отправки: {fb_err}"
                        error_log += f"Fallback Send Error: {fb_err}\n"
                    tlog(f"\033[91m[-] Ошибка движка ({btn_err}). Фолбэк: {fb_msg}\033[0m")
                    error_log += f"Engine Action Error: {btn_err}\n"

        except Exception as queue_err:
            error_msg = f"Критическая ошибка обработки анкеты: {queue_err}"
            print(f"\033[91m[-] {error_msg}\033[0m")
            error_log += f"{error_msg}\n"
        finally:
            # ── Запись в историю вынесена в finally для гарантии записи ──
            write_history_log(
                service_name=service_name,
                action=action,
                reason=reason,
                profile_text=profile_text,
                photo_path=photo_path or "",
                tg_message_raw=tg_raw_text,
                script_response=script_response,
                terminal_log="\n".join(terminal_lines),
                error_log=error_log
            )
            profile_queue.task_done()


# ───────────────────────────────────────────────
# Основной цикл прослушки одного бота
# ───────────────────────────────────────────────

async def process_dating_bot(client, engine, is_test: bool, delay_range: tuple, service_name: str) -> str:
    """
    Открывает прослушку бота, обрабатывает анкеты через queue_worker.
    
    Возвращает:
        "LIMIT_REACHED"    — лимит исчерпан, переключаемся на следующий сервис
        "STOPPED_BY_USER"  — пользователь нажал '0'
        "ERROR"            — критическая ошибка
    """
    target_bot = engine.target_bot
    print(f"\033[90m[*] Поиск диалога с @{target_bot}...\033[0m")

    try:
        bot_entity = await client.get_entity(target_bot)
        print(f"\033[92m[🟢] Подключение установлено. Слушаю анкеты...\033[0m\n")

        # Множество для фильтрации дублей фото в альбомах (берём только первое)
        processed_grouped_ids: set = set()

        # Запускаем фоновый воркер
        worker_task = asyncio.create_task(
            queue_worker(client, bot_entity, is_test, delay_range, engine, service_name)
        )
        limit_reached_event = asyncio.Event()

        async def handler(event):
            """Хэндлер входящих сообщений от бота"""
            if getattr(event, 'sender_id', None) != bot_entity.id:
                return
            if not hasattr(event, 'message') or not event.message:
                return

            # Проверяем тип сообщения через движок
            trigger_status = await engine.check_triggers(event, is_test)

            if trigger_status == "limit":
                print(f"\n\033[93m[⚠️] Триггер лимита в @{target_bot}!\033[0m")
                limit_reached_event.set()
                return
            elif trigger_status == "ad":
                print(f"\n\033[93m[!] Реклама — пропуск.\033[0m")
                return
            elif trigger_status == "match":
                print(f"\n\033[95m[🎉] МЭТЧ!\033[0m\a")
                if event.message.message:
                    print(f"\033[90m{event.message.message.replace(chr(10), ' ')}\033[0m")
                return
            elif trigger_status == "ignore":
                return

            # Фильтр дублей в альбоме — берём только первую фотку
            if event.message.grouped_id:
                if event.message.grouped_id in processed_grouped_ids:
                    return
                processed_grouped_ids.add(event.message.grouped_id)
                if len(processed_grouped_ids) > 100:
                    processed_grouped_ids.clear()
                    processed_grouped_ids.add(event.message.grouped_id)

            # Пропускаем сообщения без контента
            if not (event.message.message or getattr(event.message, 'media', None)):
                return

            # Кидаем в очередь на обработку
            await profile_queue.put(event)

        client.add_event_handler(handler, events.NewMessage(chats=bot_entity))
        print("\033[93m[*] Конвейер запущен. Введите '0' + Enter для остановки.\033[0m")

        # Удерживаем сессию открытой — опрашиваем клавиши и событие лимита
        while not limit_reached_event.is_set():
            if msvcrt.kbhit():
                try:
                    char = msvcrt.getwche()
                    if char == '0':
                        break
                except Exception:
                    pass
            await asyncio.sleep(0.1)

        client.remove_event_handler(handler)
        worker_task.cancel()

        if limit_reached_event.is_set():
            return "LIMIT_REACHED"
        else:
            print("\033[92m[🟢] Конвейер остановлен вручную. Возвращаемся в меню...\033[0m")
            return "STOPPED_BY_USER"

    except Exception as e:
        print(f"\n\033[91m[❌] Критическая ошибка воркера: {e}\033[0m")
        return "ERROR"


# ───────────────────────────────────────────────
# Главный цикл — меню
# ───────────────────────────────────────────────

async def main_flow():
    """Главный цикл приложения: отображает меню и обрабатывает выбор пользователя."""
    global config
    while True:
        show_anime_menu()
        choice = input("\033[95m Выберите пункт меню ▸ \033[0m").strip()

        if choice == "1" or choice == "2":
            is_test = (choice == "1")

            # Выбор начального сервиса
            print("\n\033[95m[?] Выберите начального бота:\033[0m")
            for k, v in SERVICES.items():
                print(f"  {k}. {v['name']} (@{v['bot']})")
            srv_choice = input("\033[95m Роутинг ▸ \033[0m").strip()

            bot_keys = list(SERVICES.keys())
            if srv_choice not in bot_keys:
                srv_choice = bot_keys[0]
            current_bot_idx = bot_keys.index(srv_choice)

            # Выбор скорости
            print("\n\033[95m[?] Выберите режим скорости:\033[0m")
            for k, v in SPEED_MODES.items():
                print(f"  {k}. {v['name']}")
            spd_choice = input("\033[95m Скорость ▸ \033[0m").strip()
            current_delay = SPEED_MODES.get(spd_choice, SPEED_MODES["2"])["delay"]

            # ── АВТОЗАПРОС ПРОФИЛЯ (отдельная сессия, до старта воркера) ──
            engine_tmp = get_engine(bot_keys[current_bot_idx])
            await fetch_and_save_my_profile(engine_tmp)
            print()

            # ── ОСНОВНАЯ СЕССИЯ ВОРКЕРА ──
            print(f"\033[90m[*] Инициализация сессии Telethon...\033[0m")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            client = TelegramClient(
                os.path.join(script_dir, "data", "ai_agent_session"),
                api_id=config["API_ID"],
                api_hash=config["API_HASH"]
            )

            async with client:
                while True:
                    engine = get_engine(bot_keys[current_bot_idx])
                    service_name = SERVICES[bot_keys[current_bot_idx]]["name"]

                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\033[92m[🟢] ВОРКЕР АКТИВИРОВАН\033[0m")
                    print(f"🎯 Бот: \033[96m@{engine.target_bot}\033[0m | Режим: \033[95m{'ТЕСТ' if is_test else 'БОЕВОЙ'}\033[0m")
                    print(f"⏱️ Таймаут: \033[90m{current_delay[0]}-{current_delay[1]} сек\033[0m\n")

                    status = await process_dating_bot(client, engine, is_test, current_delay, service_name)

                    if status == "LIMIT_REACHED" and not is_test:
                        # Переходим к следующему сервису в очереди
                        current_bot_idx += 1
                        if current_bot_idx < len(bot_keys):
                            next_engine = get_engine(bot_keys[current_bot_idx])
                            print(f"\n\033[95m[🔄] Авто-переключение на @{next_engine.target_bot} через 5 сек...\033[0m")
                            await asyncio.sleep(5)
                            # Запрашиваем свою анкету у нового сервиса — в отдельной сессии
                            # (текущая сессия ещё открыта, поэтому используем временный клиент)
                            try:
                                tmp = TelegramClient(
                                    os.path.join(script_dir, "data", "ai_agent_session"),
                                    api_id=config["API_ID"],
                                    api_hash=config["API_HASH"]
                                )
                                async with tmp:
                                    await next_engine.fetch_profile(tmp)
                                    # Результат автоматически сохраняется внутри fetch_profile
                                    # Но нам нужен и сохранение — дублируем логику
                                    print(f"\033[90m[*] Профиль у @{next_engine.target_bot} обновлён\033[0m")
                                await next_engine.start(client)
                            except Exception as sw_err:
                                print(f"\033[91m[-] Ошибка при переключении: {sw_err}\033[0m")
                            continue
                        else:
                            print(f"\n\033[91m[❌] Все сервисы исчерпали лимиты!\033[0m")
                            break
                    else:
                        break

            input("\n\033[90mНажмите Enter для возврата в меню...\033[0m")

        elif choice == "3":
            # Тест записи истории — убеждаемся что файл создаётся и пишется
            print("\n\033[90m[*] Тест записи history.md...\033[0m")
            write_history_log(
                service_name="ТЕСТ",
                action="like",
                reason="Тестовая запись для проверки работы истории",
                profile_text="Тестовая анкета\nИмя: Тест\nВозраст: 18",
                photo_path="",
                tg_message_raw="Тестовое сообщение из TG",
                script_response="тест-запись",
                terminal_log="Эта строка сгенерирована пунктом 3 меню",
            )
            script_dir = os.path.dirname(os.path.abspath(__file__))
            history_path = os.path.join(script_dir, "data", "history.md")
            if os.path.exists(history_path):
                print(f"\033[92m[🟢] Запись успешна! Файл: {history_path}\033[0m")
            else:
                print(f"\033[91m[❌] Файл не создан: {history_path}\033[0m")
            input("\n\033[90mНажмите Enter...\033[0m")

        elif choice == "4":
            # Сброс настроек .env и перезапуск Setup Wizard
            confirm = input("\033[91m[!] Сбросить .env? (y/n): \033[0m").strip().lower()
            if confirm == 'y':
                if os.path.exists(".env"):
                    os.remove(".env")
                    print("\033[92m[🟢] .env удалён. Запускаем Setup Wizard...\033[0m")
                    config = load_config()
            input("\n\033[90mНажмите Enter...\033[0m")

        elif choice == "5":
            print("\n\033[91mВыход. До связи!\033[0m")
            sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main_flow())
    except KeyboardInterrupt:
        print("\n\033[91mПрограмма завершена пользователем.\033[0m")
        sys.exit(0)