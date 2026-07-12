import asyncio
from telethon.errors import MessageNotModifiedError
from .base import BotEngine

class BlurEngine(BotEngine):
    """Движок для бота @blurrr_dating_bot — взаимодействие через инлайн-кнопки"""

    @property
    def target_bot(self) -> str:
        """Telegram username бота Blurrr"""
        return "blurrr_dating_bot"

    @property
    def vlm_mode(self) -> str:
        """Режим VLM: бинарный лайк/дизлайк"""
        return "binary"

    async def start(self, client):
        """Отправка команды боту для начала показа анкет (согласно реплай-кнопке)"""
        bot_entity = await client.get_entity(self.target_bot)
        # На скрине пробела после эмодзи нет
        await client.send_message(bot_entity, "👀Искать")

    async def fetch_profile(self, client) -> str:
        """Запрос текста собственной анкеты пользователя."""
        try:
            bot_entity = await client.get_entity(self.target_bot)
            await client.send_message(bot_entity, "/profile")
            await asyncio.sleep(4)
            messages = await client.get_messages(bot_entity, limit=5)
            for msg in messages:
                if getattr(msg, 'sender_id', None) == bot_entity.id and getattr(msg, 'photo', None) and msg.text:
                    profile_text = msg.text
                    return profile_text
        except Exception as e:
            print(f"[BlurEngine] Ошибка в fetch_profile: {e}")
        return ""

    async def check_triggers(self, event, is_test: bool) -> str:
        """Определяет тип входящего сообщения от бота."""
        text_content = event.message.message or ""
        
        # Проверка триггеров лимита и бустов
        if ("анкеты закончились" in text_content.lower()
                or "лайков на сегодня" in text_content.lower()
                or "активируйте буст" in text_content.lower()
                or "лимит" in text_content.lower()):
            return "limit"

        # Проверка рекламы
        if "lovesta" in text_content.lower() or "премиум" in text_content.lower():
            if getattr(event.message, 'buttons', None) and not is_test:
                try:
                    await event.message.buttons[0][0].click()
                    await asyncio.sleep(1)
                except Exception:
                    pass
            return "ad"

        # Проверка мэтчей
        if "взаимный лайк" in text_content.lower() or "симпатия" in text_content.lower() or "мэтч" in text_content.lower():
            return "match"

        # ЖЕСТКАЯ ПРОВЕРКА НА АНКЕТУ:
        # У анкеты ДОЛЖНО быть фото и ряд из 4-х инлайн кнопок: 🗑️, 💌, ❤️‍🔥, 💗
        buttons = getattr(event.message, 'buttons', None)
        if getattr(event.message, 'photo', None) and buttons and len(buttons) > 0 and len(buttons[0]) >= 4:
            return "profile"

        return "ignore"

    async def click_action(self, event, action: str):
        """
        Нажимает нужную кнопку в зависимости от вердикта VLM.
        Индексы кнопок по скрину:
        0: 🗑️ (дизлайк)
        1: 💌 (сообщение)
        2: ❤️‍🔥 (суперлайк)
        3: 💗 (обычный лайк)
        """
        buttons = getattr(event, 'buttons', getattr(event.message, 'buttons', None))
        if not buttons or not buttons[0]:
            return

        try:
            if action == "like":
                # Бьем четко по 4-й кнопке (индекс 3) для обычного лайка
                if len(buttons[0]) >= 4:
                    await buttons[0][3].click()
                else:
                    # Фолбэк, если кнопок внезапно стало меньше
                    await buttons[0][-1].click()
            else:
                # Дизлайк — это всегда самая первая кнопка (индекс 0)
                await buttons[0][0].click()
                
            # КРИТИЧНО: Задержка, чтобы Телеграм и бот успели схавать коллбек
            await asyncio.sleep(1.5)
            
        except MessageNotModifiedError:
            # Обычная история для телетона, игнорим
            pass
        except Exception as e:
            print(f"[BlurEngine] Ошибка при клике: {e}")