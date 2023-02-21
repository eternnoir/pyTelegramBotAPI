import urllib.parse
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Awaitable, Callable, Coroutine, Optional

from aiohttp import hdrs
from aiohttp.typedefs import Handler as AiohttpHandler

from telebot import AsyncTeleBot
from telebot.metrics import TelegramUpdateMetrics
from telebot.util import create_error_logging_task


@dataclass
class AuxBotEndpoint:
    method: str
    route: str  # with leading slash
    handler: AiohttpHandler

    def __post_init__(self):
        if self.method not in hdrs.METH_ALL:
            raise ValueError(f"Unknown method {self.method!r}")


@dataclass
class BotRunner:
    bot_prefix: str
    bot: AsyncTeleBot
    background_jobs: list[Coroutine[None, None, None]] = field(default_factory=list)
    aux_endpoints: list[AuxBotEndpoint] = field(default_factory=list)
    metrics_handler: Optional[Callable[[TelegramUpdateMetrics], Awaitable[None]]] = None

    def __post_init__(self):
        if self.bot.log_marker is None:
            self.bot.log_marker = self.bot_prefix

    async def run_polling(self):
        """For local run / testing only"""
        background_job_tasks = [
            create_error_logging_task(job, name=f"{self.bot_prefix}-{idx + 1}")
            for idx, job in enumerate(self.background_jobs)
        ]
        try:
            await self.bot.infinity_polling(interval=1)
        finally:
            for t in background_job_tasks:
                if t.cancel():
                    await t

    @property
    def bot_prefix_urlsafe(self) -> str:
        return urllib.parse.quote("-".join(self.bot_prefix.split()))

    def webhook_subroute(self) -> str:
        token_hash = sha256(self.bot.token.encode("utf-8")).hexdigest()
        return f"{self.bot_prefix_urlsafe}-{token_hash}"
