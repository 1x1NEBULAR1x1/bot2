import datetime
from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from db import get_antispam, get_time_limit


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.5):
        self.time_updates: dict[int, datetime.datetime] = {}
        self.timedelta_limiter = datetime.timedelta(milliseconds=limit*1000.0)

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        if await get_time_limit():
            limit = (await get_time_limit())[0] * 1000.0
            self.timedelta_limiter = datetime.timedelta(milliseconds=limit)
        if isinstance(event, (Message, CallbackQuery)):
            if await get_antispam():
                if (await get_antispam())[0] == 1:
                    user_id = event.from_user.id
                    if user_id in self.time_updates.keys():
                        if (datetime.datetime.now() - self.time_updates[user_id]) > self.timedelta_limiter:
                            self.time_updates[user_id] = datetime.datetime.now()
                            return await handler(event, data)
                        else:
                            return
                    else:
                        self.time_updates[user_id] = datetime.datetime.now()
                        return await handler(event, data)
                else:
                    return await handler(event, data)
            else:
                return await handler(event, data)
        return await handler(event, data)