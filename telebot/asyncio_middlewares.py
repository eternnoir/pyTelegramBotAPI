class BaseMiddleware:
    """
    Base class for middleware.

    Your middlewares should be inherited from this class.
    """

    def __init__(self):
        pass

    async def pre_process(self, message, data):
        raise NotImplementedError

    async def post_process(self, message, data, exception):
        raise NotImplementedError
