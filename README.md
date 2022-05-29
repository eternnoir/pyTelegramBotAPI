<p align="center">
  <a href="https://pypi.org/project/telebot-against-war/">
    <img src="https://img.shields.io/pypi/v/telebot-against-war.svg" alt="PyPI package version"/>
  </a>
  <a href="https://pypi.org/project/telebot-against-war/">
    <img src="https://img.shields.io/pypi/pyversions/telebot-against-war.svg" alt="Supported Python versions"/>
  </a>
</p>

# <p align="center">telebot

<p align="center">Async-first fork of <a href="https://github.com/eternnoir/pyTelegramBotAPI">pyTelegramBotApi</a>
library wrapping the <a href="https://core.telegram.org/bots/api">Telegram Bot API</a>.</p>

<p align="center">Supported Bot API version: <a href="https://core.telegram.org/bots/api#april-16-2022">6.0</a>!

<h2 align="center">See upstream project <a href='https://pytba.readthedocs.io/en/latest/index.html'>docs</a> and 
<a href='https://github.com/eternnoir/pyTelegramBotAPI/blob/master/README.md'>README</a></h2>


## Usage

Install with

```bash
pip install telebot-against-war
```

Basic usage

```python
import asyncio
from telebot import AsyncTeleBot, types


async def minimal_example():
    bot = AsyncTeleBot("TOKEN")

    @bot.message_handler(commands=["start", "help"])
    async def receive_cmd(m: types.Message):
        await bot.send_message(m.from_user.id, "Welcome!")


    @bot.message_handler()  # catch-all handler
    def receive_message(m: types.Message):
        await bot.reply_to(m, m.text)

    await bot.infinity_polling(interval=1)


asyncio.run(minimal_example())

```


## Development

The project uses [Poetry](https://python-poetry.org/) to manage dependencies, build and publish the package.
Install as described [here](https://python-poetry.org/docs/master/#installation) and make sure to update
to the latest `1.2.x` version:

```bash
poetry self update 1.2.0b1
```


### Installing and configuring locally

```bash
poetry install
poetry run pre-commit install
```

### Running tests and linters

```bash
poetry shell

pytest tests -vv

mypy telebot

black .
isort .
```

### Building

```bash
poetry plugin add poetry-dynamic-versioning
poetry build
poetry publish -u <pypi-username> -p <pypi-pwd>
```
