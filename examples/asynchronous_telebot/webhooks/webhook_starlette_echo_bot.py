#!/usr/bin/env python
"""
Asynchronous Telegram Echo Bot example.

This is a simple bot that echoes each message that is received onto the chat.
It uses the Starlette ASGI framework to receive updates via webhook requests.
"""

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, Update

API_TOKEN = "TOKEN"

WEBHOOK_HOST = "<ip/domain>"
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_SSL_CERT = "./webhook_cert.pem"  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = "./webhook_pkey.pem"  # Path to the ssl private key
WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}/telegram"
WEBHOOK_SECRET_TOKEN = "SECRET_TOKEN"

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = AsyncTeleBot(token=API_TOKEN)

# BOT HANDLERS
@bot.message_handler(commands=["help", "start"])
async def send_welcome(message: Message):
    """
    Handle '/start' and '/help'
    """
    await bot.reply_to(
        message,
        ("Hi there, I am EchoBot.\n" "I am here to echo your kind words back to you."),
    )


@bot.message_handler(func=lambda _: True, content_types=["text"])
async def echo_message(message: Message):
    """
    Handle all other messages
    """
    await bot.reply_to(message, message.text)


# WEBSERVER HANDLERS
async def telegram(request: Request) -> Response:
    """Handle incoming Telegram updates."""
    token_header_name = "X-Telegram-Bot-Api-Secret-Token"
    if request.headers.get(token_header_name) != WEBHOOK_SECRET_TOKEN:
        return PlainTextResponse("Forbidden", status_code=403)
    await bot.process_new_updates([Update.de_json(await request.json())])
    return Response()


async def startup() -> None:
    """Register webhook for telegram updates."""
    webhook_info = await bot.get_webhook_info(30)
    if WEBHOOK_URL != webhook_info.url:
        logger.debug(
            f"updating webhook url, old: {webhook_info.url}, new: {WEBHOOK_URL}"
        )
        if not await bot.set_webhook(
            url=WEBHOOK_URL, secret_token=WEBHOOK_SECRET_TOKEN
        ):
            raise RuntimeError("unable to set webhook")


app = Starlette(
    routes=[
        Route("/telegram", telegram, methods=["POST"]),
    ],
    on_startup=[startup],
)


uvicorn.run(
    app,
    host=WEBHOOK_HOST,
    port=WEBHOOK_LISTEN,
    ssl_certfile=WEBHOOK_SSL_CERT,
    ssl_keyfile=WEBHOOK_SSL_PRIV,
)
