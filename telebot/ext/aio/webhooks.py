"""
This file is used by AsyncTeleBot.run_webhooks() function.

Fastapi and starlette(0.20.2+) libraries are required to run this script.
"""

# modules required for running this script
fastapi_installed = True
try:
    import fastapi
    from fastapi.responses import JSONResponse
    from fastapi.requests import Request
    from uvicorn import Server, Config
except ImportError:
    fastapi_installed = False

import asyncio


from telebot.types import Update


from typing import Optional


class AsyncWebhookListener:
    def __init__(self, bot, 
                secret_token: str, host: Optional[str]="127.0.0.1", 
                port: Optional[int]=443,
                ssl_context: Optional[tuple]=None,
                url_path: Optional[str]=None,
                ) -> None:
        """
        Aynchronous implementation of webhook listener
        for asynchronous version of telebot.
        Not supposed to be used manually by user.
        Use AsyncTeleBot.run_webhooks() instead.

        :param bot: AsyncTeleBot instance.
        :type bot: telebot.async_telebot.AsyncTeleBot

        :param secret_token: Telegram secret token
        :type secret_token: str

        :param host: Webhook host
        :type host: str

        :param port: Webhook port
        :type port: int

        :param ssl_context: SSL context
        :type ssl_context: tuple

        :param url_path: Webhook url path
        :type url_path: str

        :raises ImportError: If FastAPI or uvicorn is not installed.
        :raises ImportError: If Starlette version is too old.

        :return: None
        """
        self._check_dependencies()

        self.app = fastapi.FastAPI()
        self._secret_token = secret_token
        self._bot = bot
        self._port = port
        self._host = host
        self._ssl_context = ssl_context
        self._url_path = url_path
        self._prepare_endpoint_urls()


    def _check_dependencies(self):
        if not fastapi_installed:
            raise ImportError('Fastapi or uvicorn is not installed. Please install it via pip.')
            
        import starlette
        if starlette.__version__ < '0.20.2':
            raise ImportError('Starlette version is too old. Please upgrade it: `pip3 install starlette -U`')
        return

    
    def _prepare_endpoint_urls(self):
        self.app.add_api_route(endpoint=self.process_update,path= self._url_path, methods=["POST"])


    async def process_update(self, request: Request, update: dict):
        """
        Processes updates.

        :meta private:
        """
        # header containsX-Telegram-Bot-Api-Secret-Token
        if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != self._secret_token:
            # secret token didn't match
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
        if request.headers.get('content-type') == 'application/json':
            json_string = update
            asyncio.create_task(self._bot.process_new_updates([Update.de_json(json_string)]))
            return JSONResponse('', status_code=200)

        return JSONResponse(status_code=403, content={"error": "Forbidden"})


    async def run_app(self):
        """
        Run app with the given parameters to init.
        Not supposed to be used manually by user.

        :return: None
        """

        config = Config(app=self.app,
            host=self._host,
            port=self._port,
            ssl_certfile=self._ssl_context[0],
            ssl_keyfile=self._ssl_context[1]
        )
        server = Server(config)
        await server.serve()
        await self._bot.close_session()