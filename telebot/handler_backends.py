import os
import pickle
import threading

from telebot import apihelper
try:
    from redis import Redis
    redis_installed = True
except:
    redis_installed = False


class HandlerBackend(object):
    """
    Class for saving (next step|reply) handlers.

    :meta private:
    """
    def __init__(self, handlers=None):
        if handlers is None:
            handlers = {}
        self.handlers = handlers

    def register_handler(self, handler_group_id, handler):
        raise NotImplementedError()

    def clear_handlers(self, handler_group_id):
        raise NotImplementedError()

    def get_handlers(self, handler_group_id):
        raise NotImplementedError()


class MemoryHandlerBackend(HandlerBackend):
    """
    :meta private:
    """
    def register_handler(self, handler_group_id, handler):
        if handler_group_id in self.handlers:
            self.handlers[handler_group_id].append(handler)
        else:
            self.handlers[handler_group_id] = [handler]

    def clear_handlers(self, handler_group_id):
        self.handlers.pop(handler_group_id, None)

    def get_handlers(self, handler_group_id):
        return self.handlers.pop(handler_group_id, None)

    def load_handlers(self, filename, del_file_after_loading):
        raise NotImplementedError()


class FileHandlerBackend(HandlerBackend):
    """
    :meta private:
    """
    def __init__(self, handlers=None, filename='./.handler-saves/handlers.save', delay=120):
        super(FileHandlerBackend, self).__init__(handlers)
        self.filename = filename
        self.delay = delay
        self.timer = threading.Timer(delay, self.save_handlers)

    def register_handler(self, handler_group_id, handler):
        if handler_group_id in self.handlers:
            self.handlers[handler_group_id].append(handler)
        else:
            self.handlers[handler_group_id] = [handler]
        self.start_save_timer()

    def clear_handlers(self, handler_group_id):
        self.handlers.pop(handler_group_id, None)
        self.start_save_timer()

    def get_handlers(self, handler_group_id):
        handlers = self.handlers.pop(handler_group_id, None)
        self.start_save_timer()
        return handlers

    def start_save_timer(self):
        if not self.timer.is_alive():
            if self.delay <= 0:
                self.save_handlers()
            else:
                self.timer = threading.Timer(self.delay, self.save_handlers)
                self.timer.start()

    def save_handlers(self):
        self.dump_handlers(self.handlers, self.filename)

    def load_handlers(self, filename=None, del_file_after_loading=True):
        if not filename:
            filename = self.filename
        tmp = self.return_load_handlers(filename, del_file_after_loading=del_file_after_loading)
        if tmp is not None:
            self.handlers.update(tmp)

    @staticmethod
    def dump_handlers(handlers, filename, file_mode="wb"):
        dirs = filename.rsplit('/', maxsplit=1)[0]
        os.makedirs(dirs, exist_ok=True)

        with open(filename + ".tmp", file_mode) as file:
            if (apihelper.CUSTOM_SERIALIZER is None):
                pickle.dump(handlers, file)
            else:
                apihelper.CUSTOM_SERIALIZER.dump(handlers, file)

        if os.path.isfile(filename):
            os.remove(filename)

        os.rename(filename + ".tmp", filename)

    @staticmethod
    def return_load_handlers(filename, del_file_after_loading=True):
        if os.path.isfile(filename) and os.path.getsize(filename) > 0:
            with open(filename, "rb") as file:
                if (apihelper.CUSTOM_SERIALIZER is None):
                    handlers = pickle.load(file)
                else:
                    handlers = apihelper.CUSTOM_SERIALIZER.load(file)

            if del_file_after_loading:
                os.remove(filename)

            return handlers


class RedisHandlerBackend(HandlerBackend):
    """
    :meta private:
    """
    def __init__(self, handlers=None, host='localhost', port=6379, db=0, prefix='telebot', password=None):
        super(RedisHandlerBackend, self).__init__(handlers)
        if not redis_installed:
            raise Exception("Redis is not installed. Install it via 'pip install redis'")
        self.prefix = prefix
        self.redis = Redis(host, port, db, password)

    def _key(self, handle_group_id):
        return ':'.join((self.prefix, str(handle_group_id)))

    def register_handler(self, handler_group_id, handler):
        handlers = []
        value = self.redis.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
        handlers.append(handler)
        self.redis.set(self._key(handler_group_id), pickle.dumps(handlers))

    def clear_handlers(self, handler_group_id):
        self.redis.delete(self._key(handler_group_id))

    def get_handlers(self, handler_group_id):
        handlers = None
        value = self.redis.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
            self.clear_handlers(handler_group_id)
        return handlers


class State:
    """
    Class representing a state.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """
    def __init__(self) -> None:
        self.name = None
    def __str__(self) -> str:
        return self.name


class StatesGroup:
    """
    Class representing common states.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """
    def __init_subclass__(cls) -> None:
        state_list = []
        for name, value in cls.__dict__.items():
            if not name.startswith('__') and not callable(value) and isinstance(value, State):
                # change value of that variable
                value.name = ':'.join((cls.__name__, name))
                value.group = cls
                state_list.append(value)
        cls._state_list = state_list

    @property
    def state_list(self):
        return self._state_list


class BaseMiddleware:
    """
    Base class for middleware.
    Your middlewares should be inherited from this class.

    Set update_sensitive=True if you want to get different updates on
    different functions. For example, if you want to handle pre_process for
    message update, then you will have to create pre_process_message function, and
    so on. Same applies to post_process.

    .. note::
        If you want to use middleware, you have to set use_class_middlewares=True in your
        TeleBot instance.

    .. code-block:: python3
        :caption: Example of class-based middlewares.

        class MyMiddleware(BaseMiddleware):
            def __init__(self):
                self.update_sensitive = True
                self.update_types = ['message', 'edited_message']
            
            def pre_process_message(self, message, data):
                # only message update here
                pass

            def post_process_message(self, message, data, exception):
                pass # only message update here for post_process

            def pre_process_edited_message(self, message, data):
                # only edited_message update here
                pass

            def post_process_edited_message(self, message, data, exception):
                pass # only edited_message update here for post_process
    """

    update_sensitive: bool = False

    def __init__(self):
        pass

    def pre_process(self, message, data):
        raise NotImplementedError

    def post_process(self, message, data, exception):
        raise NotImplementedError


class SkipHandler:
    """
    Class for skipping handlers.
    Just return instance of this class 
    in middleware to skip handler.
    Update will go to post_process,
    but will skip execution of handler.
    """
    def __init__(self) -> None:
        pass


class CancelUpdate:
    """
    Class for canceling updates.
    Just return instance of this class 
    in middleware to skip update.
    Update will skip handler and execution
    of post_process in middlewares.
    """
    def __init__(self) -> None:
        pass


class ContinueHandling:
    """
    Class for continue updates in handlers.
    Just return instance of this class 
    in handlers to continue process.
    
    .. code-block:: python3
        :caption: Example of using ContinueHandling

        @bot.message_handler(commands=['start'])
        def start(message):
            bot.send_message(message.chat.id, 'Hello World!')
            return ContinueHandling()
        
        @bot.message_handler(commands=['start'])
        def start2(message):
            bot.send_message(message.chat.id, 'Hello World2!')
    
    """
    def __init__(self) -> None:
        pass
