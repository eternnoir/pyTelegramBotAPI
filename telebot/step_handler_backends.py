class StepHandlerBaseBackend(object):
    def register_handler(self, chat_id, callback):
        raise NotImplementedError()

    def clear_handler(self, chat_id):
        raise NotImplementedError()

    def get_handlers(self, chat_id):
        raise NotImplementedError()


class StepHandlerMemoryBackend(StepHandlerBaseBackend):
    _callbacks = {}

    def register_handler(self, chat_id, callback):
        if chat_id in self._callbacks:
            self._callbacks[chat_id].append(callback)
        else:
            self._callbacks[chat_id] = [callback]

    def clear_handler(self, chat_id):
        self._callbacks[chat_id] = []

    def get_handlers(self, chat_id):
        return self._callbacks.get(chat_id, [])


class StepHandlerRedisBackend(StepHandlerBaseBackend):
    _callbacks = {}

    @classmethod
    def add_handler(cls, callback):
        cls._callbacks[callback.__name__] = callback
        return callback

    @classmethod
    def add_handlers(cls, *callbacks):
        for callback in callbacks:
            cls.add_handler(callback)

    def __init__(self, host='localhost', port=6379, db=0, prefix='telebot'):
        from redis import Redis
        self.prefix = str(prefix)
        self.redis = Redis(host, port, db)

    def _get_key(self, chat_id):
        return ':'.join((self.prefix, str(chat_id)))

    def register_handler(self, chat_id, callback):
        self.redis.sadd(self._get_key(chat_id), callback.__name__)

    def clear_handler(self, chat_id):
        self.redis.delete(self._get_key(chat_id))

    def get_handlers(self, chat_id):
        lst = self.redis.smembers(self._get_key(chat_id)) or []
        return [self._callbacks[name.decode()] for name in lst]
