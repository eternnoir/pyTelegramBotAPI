import asyncio
import urllib.parse
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Coroutine, Literal

from aiohttp.typedefs import Handler as AiohttpHandler

from telebot import AsyncTeleBot


@dataclass
class AuxBotEndpoint:
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
    route: str  # with leading slash
    handler: AiohttpHandler


@dataclass
class BotRunner:
    bot_prefix: str
    bot: AsyncTeleBot
    background_jobs: list[Coroutine[None, None, None]] = field(default_factory=list)
    aux_endpoints: list[AuxBotEndpoint] = field(default_factory=list)

    async def run_polling(self):
        """For local run / testing only"""
        await asyncio.gather(
            self.bot.infinity_polling(interval=1),
            *self.background_jobs,
        )

    @property
    def bot_prefix_urlsafe(self) -> str:
        return urllib.parse.quote("-".join(self.bot_prefix.split()))

    def webhook_subroute(self) -> str:
        token_hash = sha256(self.bot.token.encode("utf-8")).hexdigest()
        return f"{self.bot_prefix_urlsafe}-{token_hash}"
