import asyncio
from .base import BotEngine

class BibintoEngine(BotEngine):
    """Движок для бота @bibinto_bot — оценки анкет по шкале 1-10"""

    @property
    def target_bot(self) -> str:
        """Telegram username бота Bibinto"""
        return "bibinto_bot"

    @property
    def vlm_mode(self) -> str:
        """Режим VLM: оценка от 1 до 10 (score), а не бинарный лайк/дизлайк"""
        return "score"

    async def start(self, client):
        """Отправка стартовой команды боту для начала показа анкет"""
        bot_entity = await client.get_entity(self.target_bot)
        await client.send_message(bot_entity, "🚀 Оценивать")

    async def fetch_profile(self, client) -> str:
        """Запрос текста собственной анкеты пользователя."""
        try:
            bot_entity = await client.get_entity(self.target_bot)
            await client.send_message(bot_entity, "👤Мой профиль")
            await asyncio.sleep(4)
            messages = await client.get_messages(bot_entity, limit=5)
            for msg in messages:
                if getattr(msg, 'sender_id', None) == bot_entity.id and getattr(msg, 'photo', None) and msg.text:
                    profile_text = msg.text
                    return profile_text
        except Exception as e:
            print(f"[BibintoEngine] Ошибка в fetch_profile: {e}")
        return ""

    async def check_triggers(self, event, is_test: bool) -> str:
        """
        Определяет тип входящего сообщения от бота.
        
        Возвращает:
            "limit"   — сработал лимит оценок на сегодня
            "ad"      — рекламное сообщение (Буст анкеты, Premium и т.д.)
            "match"   — взаимная симпатия / мэтч
            "ignore"  — пустое/системное сообщение, не требует обработки
            "profile" — анкета, которую нужно отдать в VLM
        """
        text_content = event.message.message or ""

        # Проверка триггеров лимита оценок
        if ("лимит оценок" in text_content.lower()
                or "оценки закончились" in text_content.lower()
                or "лимит исчерпан" in text_content.lower()
                or "хватит оценок" in text_content.lower()
                or "лимит лайков" in text_content.lower()):
            return "limit"

        # Проверка рекламных сообщений
        if ("Буст анкеты" in text_content
                or "Premium-статус" in text_content
                or "Активируй Premium" in text_content):
            # В боевом режиме — пытаемся безопасно пропустить рекламу
            if event.message.buttons and not is_test:
                try:
                    for row in event.message.buttons:
                        for btn in row:
                            label = btn.text.lower()
                            if "оценивать" in label or "продолжить" in label:
                                await btn.click()
                                return "ad"
                except Exception:
                    pass
            return "ad"

        # Проверка мэтчей
        if "симпатия" in text_content.lower() or "можете общаться" in text_content.lower():
            return "match"

        # Игнорируем пустые сообщения без медиа
        if not text_content and not getattr(event.message, 'media', None):
            return "ignore"

        return "profile"

    async def click_action(self, event, action: str):
        """
        Отправляет оценку боту через текстовое сообщение.

        Правила маппинга:
            dislike / skip -> "оценка 3" (мягкий скип без вылета в меню)
            like          -> "оценка 8"
            скор 1-5      -> "оценка 3"
            скор 6       -> 7
            скор 7       -> 7
            скор 8       -> 8
            скор 9,10    -> 9
        """
        if action in ["dislike", "skip"]:
            await event.respond("3")
        elif action == "like":
            await event.respond("8")
        else:
            # Числовой скор от VLM: перемапируем в безопасный диапазон 3-9
            try:
                score = int(action)
            except (ValueError, TypeError):
                await event.respond("3")
                return

            if score <= 5:
                await event.respond("3")
            elif score <= 7:
                await event.respond("7")
            elif score == 8:
                await event.respond("8")
            else:  # 9, 10
                await event.respond("9")
