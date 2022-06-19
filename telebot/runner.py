import asyncio
import urllib.parse
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Coroutine, Literal

from aiohttp.typedefs import Handler as AiohttpHandler

from telebot import AsyncTeleBot


@dataclass
class BotEndpoint:
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    subroute: str  # relative to baseurl/aux/, must not start with slash
    handler: AiohttpHandler


@dataclass
class BotRunner:
    name: str
    bot: AsyncTeleBot
    background_jobs: list[Coroutine[None, None, None]] = field(default_factory=list)
    aux_endpoints: list[BotEndpoint] = field(default_factory=list)

    async def run_polling(self):
        """For local run / testing only"""
        await asyncio.gather(
            self.bot.infinity_polling(interval=1),
            *self.background_jobs,
        )

    @property
    def name_urlsafe(self) -> str:
        return urllib.parse.quote("-".join(self.name.split()))

    def webhook_subroute(self) -> str:
        token_hash = sha256(self.bot.token.encode("utf-8")).hexdigest()
        return f"{self.name_urlsafe}-{token_hash}"
