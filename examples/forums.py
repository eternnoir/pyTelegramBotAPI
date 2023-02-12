import asyncio
import logging
import os
import uuid

from dotenv import load_dotenv

from telebot import AsyncTeleBot
from telebot import types as tg
from telebot.runner import BotRunner
from telebot.types import constants as tg_const

load_dotenv()

bot = AsyncTeleBot(os.environ["TOKEN"])

logging.basicConfig(level=logging.DEBUG)


bot_run_id = uuid.uuid4().hex[:6]
# this example bot creates three topics on each run, prefixing them with run id
topic_ids: dict[str, int] = dict()
chat_id = int(os.environ["GROUP_ID"])


@bot.message_handler(chat_types=[tg_const.ChatType.group, tg_const.ChatType.supergroup], chat_id=chat_id)
async def forward_message_to_topic(message: tg.Message):
    message_words = message.text_content.split()
    if not message_words:
        return
    bad_words_count = sum(1 if word.lower() in {"bad", "sad", "shit", "fuck"} else 0 for word in message_words)
    good_words_count = sum(1 if word.lower() in {"good", "cool", "hi", "thank"} else 0 for word in message_words)
    if bad_words_count == good_words_count == 0:
        topic_id = topic_ids.get("neutral")
    elif bad_words_count > good_words_count:
        topic_id = topic_ids.get("bad")
    else:
        topic_id = topic_ids.get("good")

    await bot.forward_message(
        chat_id=message.chat.id,
        from_chat_id=message.chat.id,
        message_id=message.id,
        message_thread_id=topic_id,
    )


async def setup_topics() -> None:
    stickers_by_emoji = {s.emoji: s for s in await bot.get_forum_topic_icon_stickers()}
    for sentiment, color, emoji in (
        ("good", 7322096, "🦄"),
        ("neutral", 16766590, "⚽"),
        ("bad", 13338331, "👀"),
    ):
        topic = await bot.create_forum_topic(
            chat_id=chat_id,
            name=f"[{bot_run_id}] {sentiment} messages",
            icon_color=color,
            icon_custom_emoji_id=stickers_by_emoji[emoji].custom_emoji_id if emoji in stickers_by_emoji else None,
        )
        topic_ids[sentiment] = topic.message_thread_id
    print(f"{topic_ids = }")
    await bot.send_message(
        chat_id=chat_id,
        text=f"current bot run id: <code>{bot_run_id}</code>",
        parse_mode="HTML",
    )


asyncio.run(BotRunner(bot_prefix="echo-bot", bot=bot, background_jobs=[setup_topics()]).run_polling())
