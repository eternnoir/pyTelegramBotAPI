"""
This file is used by AsyncTeleBot.run_webhooks() function.

Starlette(0.20.2+) and uvicorn libraries are required to run this script.
"""

# modules required for running this script
deps_installed = True
try:
    from starlette import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from uvicorn import Config, Server
except ImportError:
    deps_installed = False


from typing import Optional

from telebot.types import Update


class AsyncWebhookListener:
    def __init__(
        self,
        bot,
        secret_token: str,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = 443,
        ssl_context: Optional[tuple] = None,
        url_path: Optional[str] = None,
        debug: Optional[bool] = False,
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

        :param debug: Debug mode
        :type debug: bool

        :raises ImportError: If Starlette or uvicorn is not installed.
        :raises ImportError: If Starlette version is too old.

        :return: None
        """
        self._check_dependencies()

        self.app = Starlette()
        self._secret_token = secret_token
        self._bot = bot
        self._port = port
        self._host = host
        self._ssl_context = ssl_context
        self._url_path = url_path
        self._debug = debug
        self._prepare_endpoint_urls()

    def _check_dependencies(self):
        if not deps_installed:
            raise ImportError(
                "Starlette or uvicorn is not installed. Please install it via pip."
            )

        import starlette

        if starlette.__version__ < "0.20.2":
            raise ImportError(
                "Starlette version is too old. Please upgrade it: `pip3 install starlette -U`"
            )
        return

    def _prepare_endpoint_urls(self):
        self.app.add_route(f"/{self._url_path}", self.process_update, methods=["POST"])

    async def process_update(self, request: Request) -> Response:
        """
        Processes updates.

        :meta private:
        """
        # header contains X-Telegram-Bot-Api-Secret-Token
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        content_type = request.headers.get("content-type")
        if (secret_token != self._secret_token) or (content_type != "application/json"):
            # secret token didn't match or wrong content type
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        json_string = await request.json()
        await self._bot.process_new_updates([Update.de_json(json_string)])
        return JSONResponse("")

    async def run_app(self):
        """
        Run app with the given parameters to init.
        Not supposed to be used manually by user.

        :return: None
        """

        config = Config(
            app=self.app,
            host=self._host,
            port=self._port,
            debug=self._debug,
            ssl_certfile=self._ssl_context[0],
            ssl_keyfile=self._ssl_context[1],
        )
        server = Server(config)
        await server.serve()
        await self._bot.close_session()
