import asyncio
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Coroutine

from telebot import AsyncTeleBot, types


@dataclass
class BotRunner:
    name: str
    bot: AsyncTeleBot
    allowed_updates: list[types.AllowedUpdateName]
    background_jobs: list[Coroutine[None, None, None]] = field(default_factory=list)

    def run_polling(self):
        """For local run only"""

        async def run():
            await asyncio.gather(
                self.bot.infinity_polling(allowed_updates=self.allowed_updates, timeout=1),
                *self.background_jobs,
            )

        asyncio.run(run())

    def webhook_route(self) -> str:
        token_hash = sha256(self.bot.token.encode("utf-8")).hexdigest()
        return f"{self.name}-{token_hash}"
