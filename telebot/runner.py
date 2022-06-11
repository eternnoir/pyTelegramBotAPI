import asyncio
import urllib.parse
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Coroutine

from telebot import AsyncTeleBot


@dataclass
class BotRunner:
    name: str
    bot: AsyncTeleBot
    background_jobs: list[Coroutine[None, None, None]] = field(default_factory=list)

    async def run_polling(self):
        """For local run / testing only"""
        await asyncio.gather(
            self.bot.infinity_polling(interval=1),
            *self.background_jobs,
        )

    def webhook_subroute(self) -> str:
        urlasafe_name = "-".join(self.name.split())
        token_hash = sha256(self.bot.token.encode("utf-8")).hexdigest()
        return urllib.parse.quote(f"{urlasafe_name}-{token_hash}")
