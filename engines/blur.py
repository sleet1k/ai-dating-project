import asyncio
from .base import BotEngine

class BlurEngine(BotEngine):
    """Движок для бота @blurrr_dating_bot — классические лайк/дизлайк"""

    @property
    def target_bot(self) -> str:
        """Telegram username бота Blurrr"""
        return "blurrr_dating_bot"

    @property
    def vlm_mode(self) -> str:
        """Режим VLM: бинарный лайк/дизлайк"""
        return "binary"

    async def start(self, client):
        """Отправка стартовой команды боту для начала показа анкет"""
        bot_entity = await client.get_entity(self.target_bot)
        await client.send_message(bot_entity, "👀 Искать")

    async def fetch_profile(self, client) -> str:
        """
        Запрос текста собственной анкеты пользователя.
        Возвращает текст анкеты или пустую строку если не удалось получить.
        """
        bot_entity = await client.get_entity(self.target_bot)
        await client.send_message(bot_entity, "📋 Профиль")
        await asyncio.sleep(4)
        messages = await client.get_messages(bot_entity, limit=5)
        for msg in messages:
            if getattr(msg, 'sender_id', None) == bot_entity.id and getattr(msg, 'photo', None) and msg.text:
                return msg.text
        return ""

    async def check_triggers(self, event, is_test: bool) -> str:
        """
        Определяет тип входящего сообщения от бота.
        
        Возвращает:
            "limit"   — сработал лимит лайков
            "ad"      — рекламное сообщение (Lovesta и т.д.)
            "match"   — взаимный лайк / мэтч
            "ignore"  — пустое/системное сообщение
            "profile" — анкета для обработки VLM
        """
        text_content = event.message.message or ""

        # Проверка триггеров лимита
        if ("анкеты закончились" in text_content.lower()
                or "лайков на сегодня" in text_content.lower()
                or "лимит лайков" in text_content.lower()):
            return "limit"

        # Проверка рекламных сообщений
        if "Lovesta" in text_content or "премиум" in text_content.lower():
            if event.message.buttons and not is_test:
                try:
                    # Пытаемся нажать "Ок" или первую кнопку для закрытия рекламы
                    await event.message.buttons[0][0].click()
                except Exception:
                    pass
            return "ad"

        # Проверка мэтчей
        if "взаимный лайк" in text_content.lower() or "симпатия" in text_content.lower():
            return "match"

        # Игнорируем пустые сообщения без медиа
        if not text_content and not getattr(event.message, 'media', None):
            return "ignore"

        return "profile"

    async def click_action(self, event, action: str):
        """
        Нажимает нужную кнопку в зависимости от вердикта VLM.
        
        Кнопки Blurrr: 🗑️ (дизлайк/скип), 📩 (суперлайк), 🔥 (лайк), 💗 (лав)
        Для лайка нажимаем 🔥, для дизлайка нажимаем 🗑️.
        """
        buttons = getattr(event, 'buttons', getattr(event.message, 'buttons', None))
        if not buttons:
            return

        if action == "like":
            target_emojis = ["🔥", "💗"]
        else:
            target_emojis = ["🗑️", "🗑"]

        for row in buttons:
            for btn in row:
                if any(em in btn.text for em in target_emojis):
                    await btn.click()
                    return

        # Фолбэк по индексам
        try:
            if action == "like" and len(buttons[0]) >= 3:
                await buttons[0][2].click()
            elif action == "dislike" and len(buttons[0]) >= 1:
                await buttons[0][0].click()
        except Exception:
            pass
