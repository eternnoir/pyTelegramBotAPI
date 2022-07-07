"""
This file is used by TeleBot.run_webhooks() &
AsyncTeleBot.run_webhooks() functions.

Flask/fastapi is required to run this script.
"""

# modules required
flask_installed = True
fastapi_installed = True
uvicorn_installed = True

try:
    import flask
    from werkzeug.serving import _TSSLContextArg
except ImportError:
    flask_installed = False
    _TSSLContextArg = None

try:
    import fastapi
    from fastapi.responses import JSONResponse
except ImportError:
    fastapi_installed = False


try:
    from uvicorn import Server, Config
except ImportError:
    uvicorn_installed = False


import asyncio
from telebot.types import Update


from typing import Optional





class SyncWebhookListener:
    def __init__(self, bot, 
                secret_token: str, host: Optional[str]="127.0.0.1", 
                port: Optional[int]=8000,
                ssl_context: Optional[_TSSLContextArg]=None,
                url_path: Optional[str]=None,
                debug: Optional[bool]=False
                ) -> None:
        """
        Synchronous implementation of webhook listener
        for synchronous version of telebot.

        :param bot: TeleBot instance
        :param secret_token: Telegram secret token
        :param host: Webhook host
        :param port: Webhook port
        :param ssl_context: SSL context
        """
        if not flask_installed:
            raise ImportError('Flask is not installed. Please install it via pip.')
        self.app = flask.Flask(__name__)
        self._secret_token = secret_token
        self._bot = bot
        self._port = port
        self._host = host
        self._ssl_context = ssl_context
        self._url_path = url_path
        self._debug = debug
        self._prepare_endpoint_urls()

    
    def _prepare_endpoint_urls(self):
        self.app.add_url_rule(self._url_path, 'index', self.process_update, methods=['POST'])


    def process_update(self):
        """
        Processes updates.
        """
        # header containsX-Telegram-Bot-Api-Secret-Token
        if flask.request.headers.get('X-Telegram-Bot-Api-Secret-Token') != self._secret_token:
            # secret token didn't match
            flask.abort(403)
        if flask.request.headers.get('content-type') == 'application/json':
            json_string = flask.request.get_data().decode('utf-8')
            self._bot.process_new_updates([Update.de_json(json_string)])
            return ''

        flask.abort(403)


    def run_app(self):
        """
        Run app with the given parameters.
        """
        self.app.run(
            host=self._host,
            port=self._port,
            ssl_context=self._ssl_context,
            debug=self._debug
        )




class AsyncWebhookListener:
    def __init__(self, bot, 
                secret_token: str, host: Optional[str]="127.0.0.1", 
                port: Optional[int]=8000,
                ssl_context: Optional[_TSSLContextArg]=None,
                url_path: Optional[str]=None,
                debug: Optional[bool]=False
                ) -> None:
        """
        Synchronous implementation of webhook listener
        for synchronous version of telebot.

        :param bot: TeleBot instance
        :param secret_token: Telegram secret token
        :param host: Webhook host
        :param port: Webhook port
        :param ssl_context: SSL context
        """
        self._check_dependencies()

        self.app = fastapi.FastAPI()
        self._secret_token = secret_token
        self._bot = bot
        self._port = port
        self._host = host
        self._ssl_context = ssl_context
        self._url_path = url_path
        self._debug = debug
        self._prepare_endpoint_urls()


    def _check_dependencies(self):
        if not fastapi_installed:
            raise ImportError('Fastapi is not installed. Please install it via pip.')
        if not uvicorn_installed:
            raise ImportError('Uvicorn is not installed. Please install it via pip.')
            
        import starlette
        if starlette.__version__ < '0.20.2':
            raise ImportError('Starlette version is too old. Please upgrade it.')
        return

    
    def _prepare_endpoint_urls(self):
        self.app.add_api_route(endpoint=self.process_update,path= self._url_path, methods=["POST"])


    async def process_update(self, request):
        """
        Processes updates.
        """
        # header containsX-Telegram-Bot-Api-Secret-Token
        if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != self._secret_token:
            # secret token didn't match
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
        if request.headers.get('content-type') == 'application/json':
            json_string = await request.json()
            asyncio.create_task(self._bot.process_new_updates([Update.de_json(json_string)]))
            return JSONResponse('', status_code=200)

        return JSONResponse(status_code=403, content={"error": "Forbidden"})


    async def run_app(self):
        """
        Run app with the given parameters.
        """

        config = Config(app=self.app,
            host=self._host,
            port=self._port,
            debug=self._debug,
            ssl_certfile=self._ssl_context[0],
            ssl_keyfile=self._ssl_context[1]
        )
        server = Server(config)
        await server.serve()
        await self._bot.close_session()