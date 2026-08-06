from abc import ABC, abstractmethod
import asyncio

class BotEngine(ABC):
    @property
    @abstractmethod
    def target_bot(self) -> str:
        """Telegram username бота (например, leomatchbot)"""
        pass

    @property
    @abstractmethod
    def vlm_mode(self) -> str:
        """Режим VLM: 'binary' или 'score'"""
        pass

    @abstractmethod
    async def start(self, client):
        """Отправка стартовой команды для запуска конвейера"""
        pass

    @abstractmethod
    async def fetch_profile(self, client) -> str:
        """Запрос своей анкеты и возврат её текста"""
        pass

    @abstractmethod
    async def check_triggers(self, event, is_test: bool) -> str:
        """
        Проверка входящего сообщения на триггеры.
        Должен вернуть:
        - "limit": сработал лимит
        - "ad": это реклама (и кнопка пропуска уже должна быть нажата движком)
        - "match": это уведомление о мэтче
        - "profile": это анкета, которую надо отдать VLM
        - "ignore": пустое или системное сообщение
        """
        pass

    @abstractmethod
    async def click_action(self, event, action: str):
        """
        Клик по нужной кнопке в зависимости от ответа VLM.
        В 'binary' это "like" или "dislike".
        В 'score' это "skip" (нажать назад) или "1"-"10".
        """
        pass
