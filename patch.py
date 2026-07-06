import sys
import os

with open('tg_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add from engines import get_engine
if 'from engines import get_engine' not in content:
    content = content.replace('from telethon import TelegramClient, events\n', 'from telethon import TelegramClient, events\nfrom engines import get_engine\n')

# Replace parse_my_profile with nothing
pmp = '''async def parse_my_profile(client, target_bot):
    print(f"\\n\\033[90m[*] Отправляю команду /myprofile боту @{target_bot}...\\033[0m")
    bot_entity = await client.get_entity(target_bot)
    await client.send_message(bot_entity, "/myprofile")
    
    print("\\033[90m[*] Ожидаю ответ от бота (4 сек)...\\033[0m")
    await asyncio.sleep(4)
    
    messages = await client.get_messages(bot_entity, limit=5)
    profile_text = ""
    for msg in messages:
        if getattr(msg, 'sender_id', None) == bot_entity.id and getattr(msg, 'photo', None) and msg.text:
            profile_text = msg.text
            break
            
    if profile_text:
        os.makedirs("data", exist_ok=True)
        with open("data/my_profile.json", "w", encoding="utf-8") as f:
            json.dump({"profile_text": profile_text}, f, ensure_ascii=False, indent=4)
        print(f"\\033[92m[🟢] Твой профиль успешно сохранен:\\033[0m\\n{profile_text}")
    else:
        print("\\033[91m[🔴] Не удалось найти текст профиля. Возможно бот ответил иначе.\\033[0m")'''
content = content.replace(pmp, '')

# queue_worker signature
content = content.replace('async def queue_worker(client, bot_entity, is_test, delay_range):', 'async def queue_worker(client, bot_entity, is_test, delay_range, engine):')
content = content.replace('result = await analyze_profile(clean_text, photo_path)', 'result = await analyze_profile(clean_text, photo_path, mode=engine.vlm_mode)')

click_old = '''            action = result.get("action", "dislike")
            reason = result.get("reason", "Нет причины")
            
            if action == "like":
                print(f" \\033[92m[❤️ LIKE]\\033[0m Причина: {reason}")
            else:
                print(f" \\033[91m[👎 DISLIKE]\\033[0m Причина: {reason}")
                
            # Ищем нужную кнопку в сообщении
            if event.message.buttons and not is_test:
                target_emojis = []
                if action == "like":
                    target_emojis = ["❤️", "like", "нравится"]
                else:
                    target_emojis = ["👎", "dislike", "нет"]

                clicked = False
                for row in event.message.buttons:
                    for btn in row:
                        btn_text_lower = btn.text.lower()
                        if any(em in btn_text_lower for em in target_emojis):
                            await btn.click()
                            clicked = True
                            break
                    if clicked:
                        break
                
                if not clicked:
                    if action == "like" and len(event.message.buttons[0]) > 2:
                        await event.message.buttons[0][2].click()
                    elif action == "dislike" and len(event.message.buttons[0]) > 0:
                        await event.message.buttons[0][0].click()'''
                        
click_new = '''            action = result.get("action", "skip" if engine.vlm_mode == "score" else "dislike")
            reason = result.get("reason", "Нет причины")
            
            if engine.vlm_mode == "score":
                action_display = f"\\033[95m[⭐ Оценка: {action}]\\033[0m"
            else:
                action_display = "\\033[92m[❤️ LIKE]\\033[0m" if action == "like" else "\\033[91m[👎 DISLIKE]\\033[0m"
            print(f" {action_display} Причина: {reason}")
            
            if not is_test:
                await engine.click_action(event, action)'''
content = content.replace(click_old, click_new)

# process_dating_bot signature
process_old = '''async def process_dating_bot(client, target_bot, is_test, delay_range):
    print(f"\\033[90m[*] Поиск диалога с @{target_bot}...\\033[0m")'''
process_new = '''async def process_dating_bot(client, engine, is_test, delay_range):
    target_bot = engine.target_bot
    print(f"\\033[90m[*] Поиск диалога с @{target_bot}...\\033[0m")'''
content = content.replace(process_old, process_new)

handler_old = '''        worker_task = asyncio.create_task(queue_worker(client, bot_entity, is_test, delay_range))
        limit_reached_event = asyncio.Event()

        async def handler(event):
            # ЖЕСТКАЯ ПРОВЕРКА: отсекаем системные статусы, берем только сообщения
            if getattr(event, 'sender_id', None) != bot_entity.id:
                return
            if not hasattr(event, 'message') or not event.message:
                return
                
            text_content = event.message.message or ""
            
            # --- ПРОВЕРКА ЛИМИТОВ ---
            if "Лимит лайков на сегодня исчерпан" in text_content or "хватит анкет" in text_content.lower():
                print(f"\\n\\033[93m[⚠️] Сработал триггер лимита лайков в @{target_bot}!\\033[0m")
                limit_reached_event.set()
                return

            # --- ПРОПУСК РЕКЛАМЫ ---
            if "Premium-статус" in text_content or "больше внимания" in text_content or "Активируй Premium" in text_content:
                print(f"\\n\\033[93m[!] Обнаружена реклама. Пытаюсь пропустить...\\033[0m")
                if event.message.buttons and not is_test:
                    try:
                        for row in event.message.buttons:
                            for btn in row:
                                if "без premium" in btn.text.lower() or "пока" in btn.text.lower():
                                    await btn.click()
                                    return
                        await event.message.buttons[0][0].click()
                    except Exception:
                        pass
                return
                
            # --- ПРОВЕРКА МЭТЧЕЙ ---
            if "Есть взаимная симпатия" in text_content:
                print(f"\\n\\033[95m[🎉] УРА! ЕСТЬ МЭТЧ!\\033[0m\\a") # \\a для системного звука
                print(f"\\033[90m{text_content.replace(chr(10), ' ')}\\033[0m")
                return'''
handler_new = '''        worker_task = asyncio.create_task(queue_worker(client, bot_entity, is_test, delay_range, engine))
        limit_reached_event = asyncio.Event()

        async def handler(event):
            if getattr(event, 'sender_id', None) != bot_entity.id:
                return
            if not hasattr(event, 'message') or not event.message:
                return
                
            trigger_status = await engine.check_triggers(event, is_test)
            
            if trigger_status == "limit":
                print(f"\\n\\033[93m[⚠️] Сработал триггер лимита в @{target_bot}!\\033[0m")
                limit_reached_event.set()
                return
            elif trigger_status == "ad":
                print(f"\\n\\033[93m[!] Обнаружена реклама. Пропуск...\\033[0m")
                return
            elif trigger_status == "match":
                print(f"\\n\\033[95m[🎉] УРА! ЕСТЬ МЭТЧ!\\033[0m\\a")
                if event.message.message:
                    print(f"\\033[90m{event.message.message.replace(chr(10), ' ')}\\033[0m")
                return
            elif trigger_status == "ignore":
                return
            
            text_content = event.message.message or ""'''
content = content.replace(handler_old, handler_new)

main_loop_old = '''            print("\\n\\033[95m[?] Выберите начального бота:\\033[0m")
            for k, v in SERVICES.items():
                print(f"  {k}. {v['name']} (@{v['bot']})")
            srv_choice = input("\\033[95m Роутинг ▸ \\033[0m").strip()
            
            bot_keys = list(SERVICES.keys())
            if srv_choice not in bot_keys:
                srv_choice = bot_keys[0]
            current_bot_idx = bot_keys.index(srv_choice)

            print("\\n\\033[95m[?] Выберите режим скорости:\\033[0m")
            for k, v in SPEED_MODES.items():
                print(f"  {k}. {v['name']}")
            spd_choice = input("\\033[95m Скорость ▸ \\033[0m").strip()
            current_delay = SPEED_MODES.get(spd_choice, SPEED_MODES["2"])["delay"]

            print(f"\\n\\033[90m[*] Инициализация сессии Telethon...\\033[0m")
            client = TelegramClient('data/ai_agent_session', api_id=config["API_ID"], api_hash=config["API_HASH"])
            
            async with client:
                while True:
                    target_bot = SERVICES[bot_keys[current_bot_idx]]["bot"]
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\\033[92m[🟢] ВОРКЕР АКТИВИРОВАН\\033[0m")
                    print(f"🎯 Бот: \\033[96m@{target_bot}\\033[0m | Режим: \\033[95m{'ТЕСТ' if is_test else 'БОЕВОЙ'}\\033[0m")
                    print(f"⏱️ Настройки таймингов: \\033[90m{current_delay[0]}-{current_delay[1]} сек\\033[0m\\n")
                    
                    status = await process_dating_bot(client, target_bot, is_test, current_delay)
                    
                    if status == "LIMIT_REACHED" and not is_test:
                        current_bot_idx += 1
                        if current_bot_idx < len(bot_keys):
                            next_bot = SERVICES[bot_keys[current_bot_idx]]["bot"]
                            print(f"\\n\\033[95m[🔄] Авто-переключение! Через 5 сек стартуем @{next_bot}...\\033[0m")
                            await asyncio.sleep(5)
                            await client.send_message(next_bot, "1")
                            continue
                        else:
                            print(f"\\n\\033[91m[❌] Все доступные сервисы исчерпали лимиты на сегодня!\\033[0m")
                            break
                    else:
                        break'''

main_loop_new = '''            print("\\n\\033[95m[?] Выберите начального бота:\\033[0m")
            for k, v in SERVICES.items():
                print(f"  {k}. {v['name']} (@{v['bot']})")
            srv_choice = input("\\033[95m Роутинг ▸ \\033[0m").strip()
            
            bot_keys = list(SERVICES.keys())
            if srv_choice not in bot_keys:
                srv_choice = bot_keys[0]
            current_bot_idx = bot_keys.index(srv_choice)

            print("\\n\\033[95m[?] Выберите режим скорости:\\033[0m")
            for k, v in SPEED_MODES.items():
                print(f"  {k}. {v['name']}")
            spd_choice = input("\\033[95m Скорость ▸ \\033[0m").strip()
            current_delay = SPEED_MODES.get(spd_choice, SPEED_MODES["2"])["delay"]

            print(f"\\n\\033[90m[*] Инициализация сессии Telethon...\\033[0m")
            client = TelegramClient('data/ai_agent_session', api_id=config["API_ID"], api_hash=config["API_HASH"])
            
            async with client:
                while True:
                    engine = get_engine(bot_keys[current_bot_idx])
                    target_bot = engine.target_bot
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\\033[92m[🟢] ВОРКЕР АКТИВИРОВАН\\033[0m")
                    print(f"🎯 Бот: \\033[96m@{target_bot}\\033[0m | Режим: \\033[95m{'ТЕСТ' if is_test else 'БОЕВОЙ'}\\033[0m")
                    print(f"⏱️ Настройки таймингов: \\033[90m{current_delay[0]}-{current_delay[1]} сек\\033[0m\\n")
                    
                    status = await process_dating_bot(client, engine, is_test, current_delay)
                    
                    if status == "LIMIT_REACHED" and not is_test:
                        current_bot_idx += 1
                        if current_bot_idx < len(bot_keys):
                            next_engine = get_engine(bot_keys[current_bot_idx])
                            print(f"\\n\\033[95m[🔄] Авто-переключение! Через 5 сек стартуем @{next_engine.target_bot}...\\033[0m")
                            await asyncio.sleep(5)
                            await next_engine.start(client)
                            continue
                        else:
                            print(f"\\n\\033[91m[❌] Все доступные сервисы исчерпали лимиты на сегодня!\\033[0m")
                            break
                    else:
                        break'''
content = content.replace(main_loop_old, main_loop_new)

option_6_old = '''        elif choice == "6":
            print("\\n\\033[95m[?] С какого бота стянуть анкету?\\033[0m")
            for k, v in SERVICES.items():
                print(f"  {k}. {v['name']} (@{v['bot']})")
            srv_choice = input("\\033[95m Выбор ▸ \\033[0m").strip()
            
            bot_keys = list(SERVICES.keys())
            if srv_choice not in bot_keys:
                srv_choice = bot_keys[0]
            target_bot = SERVICES.get(srv_choice)["bot"]
            
            client = TelegramClient('data/ai_agent_session', api_id=config["API_ID"], api_hash=config["API_HASH"])
            async with client:
                await parse_my_profile(client, target_bot)
            input("\\n\\033[90mНажмите Enter...\\033[0m")'''
option_6_new = '''        elif choice == "6":
            print("\\n\\033[95m[?] С какого бота стянуть анкету?\\033[0m")
            for k, v in SERVICES.items():
                print(f"  {k}. {v['name']} (@{v['bot']})")
            srv_choice = input("\\033[95m Выбор ▸ \\033[0m").strip()
            
            bot_keys = list(SERVICES.keys())
            if srv_choice not in bot_keys:
                srv_choice = bot_keys[0]
            
            engine = get_engine(srv_choice)
            
            client = TelegramClient('data/ai_agent_session', api_id=config["API_ID"], api_hash=config["API_HASH"])
            async with client:
                print(f"\\n\\033[90m[*] Отправляю команду боту @{engine.target_bot}...\\033[0m")
                profile_text = await engine.fetch_profile(client)
                if profile_text:
                    os.makedirs("data", exist_ok=True)
                    with open("data/my_profile.json", "w", encoding="utf-8") as f:
                        json.dump({"profile_text": profile_text}, f, ensure_ascii=False, indent=4)
                    print(f"\\033[92m[🟢] Твой профиль успешно сохранен:\\033[0m\\n{profile_text}")
                else:
                    print("\\033[91m[🔴] Не удалось найти текст профиля.\\033[0m")
            input("\\n\\033[90mНажмите Enter...\\033[0m")'''
content = content.replace(option_6_old, option_6_new)

with open('tg_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch complete")
