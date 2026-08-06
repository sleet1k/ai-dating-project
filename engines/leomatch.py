import asyncio
from .base import BotEngine

class LeomatchEngine(BotEngine):
    @property
    def target_bot(self) -> str:
        return "leomatchbot"

    @property
    def vlm_mode(self) -> str:
        return "binary"

    async def start(self, client):
        bot_entity = await client.get_entity(self.target_bot)
        await client.send_message(bot_entity, "1")

    async def fetch_profile(self, client) -> str:
        try:
            bot_entity = await client.get_entity(self.target_bot)
            await client.send_message(bot_entity, "/myprofile")
            await asyncio.sleep(4)
            messages = await client.get_messages(bot_entity, limit=5)
            for msg in messages:
                if getattr(msg, 'sender_id', None) == bot_entity.id and getattr(msg, 'photo', None) and msg.text:
                    profile_text = msg.text
                    return profile_text
        except Exception as e:
            print(f"[LeomatchEngine] Ошибка в fetch_profile: {e}")
        return ""

    async def check_triggers(self, event, is_test: bool) -> str:
        text_content = event.message.message or ""
        
        if "Лимит лайков на сегодня исчерпан" in text_content or "хватит анкет" in text_content.lower():
            return "limit"

        if "Premium-статус" in text_content or "больше внимания" in text_content or "Активируй Premium" in text_content:
            if event.message.buttons and not is_test:
                try:
                    for row in event.message.buttons:
                        for btn in row:
                            if "без premium" in btn.text.lower() or "пока" in btn.text.lower():
                                await btn.click()
                                return "ad"
                    await event.message.buttons[0][0].click()
                except Exception:
                    pass
            return "ad"

        if "Есть взаимная симпатия" in text_content:
            return "match"

        if not text_content and not getattr(event.message, 'media', None):
            return "ignore"

        return "profile"

    async def click_action(self, event, action: str):
        if action == "like":
            await event.respond("1")
        elif action == "dislike":
            await event.respond("3")
        else:
            await event.respond("3")
