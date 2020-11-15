import os
import pickle
import threading

from telebot import apihelper


class HandlerBackend(object):
    """
    Class for saving (next step|reply) handlers
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
    def __init__(self, handlers=None, host='localhost', port=6379, db=0, prefix='telebot'):
        super(RedisHandlerBackend, self).__init__(handlers)
        from redis import Redis
        self.prefix = prefix
        self.redis = Redis(host, port, db)

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
    
# The HerokuPostgress Class Support
class HerokuPostgress:
    """
    The HerokuPostgress class:
    All Methods:
        1 -? is_user
        2 -? add_user
        3 -? remove_user
        4 -? get_all_users

    Explanation:
        Method 1  >? Takes In The Chat Id And Returns True If Chat Id Is In Database Else False { String }.
        Method 2  >? Takes In The Chat Id And Add To The Database { String }.
        Method 3  >? Takes In The Chat Id And Removes From The Database { String }.
        Method 4  >? Takes In Nothing Returns A List Of All Users In Database { List / Array }.
    """
    def __init__(self, db_url):
        self.url = str(db_url)
        self.all_users = []
        if self.url.startswith('postgres://'):
            pass
        else:
            os.system('')
            print("\t  \x1B[30m\x1B[43mWarning\nInvalid Heroku PostGreSQL Url\x1B[39m\x1B[49m")

        def start() -> scoped_session:
            """
            SQL Alchemy Scoped Session Is Returned.
            :return:
            """
            engine = create_engine(self.url)
            BASE.metadata.bind = engine
            BASE.metadata.create_all(engine)
            return scoped_session(
                sessionmaker(
                    bind=engine,
                    autoflush=False
                )
            )
        BASE = declarative_base()
        self.SESSION = start()

    class _(BASE):
        __tablename__ = "ChatIds"
        chat_id = Column(String(15), primary_key=True)

        def __init__(self, chat_id):
            self.chat_id = chat_id

    def is_user(self, chat_id):
        self._.__table__.create(checkfirst=True)
        try:
            return self.SESSION.query(self.Database).filter(self.Database.chat_id == str(chat_id)).one()
        except Exception:
            return False
        finally:
            self.SESSION.close()

    def add_user(self, chat_id):
        self._.__table__.create(checkfirst=True)
        adder = self.Database(str(chat_id))
        self.SESSION.add(adder)
        self.SESSION.commit()

    def remove_user(self, chat_id):
        self._.__table__.create(checkfirst=True)
        rem = self.SESSION.query(self.Database).get(str(chat_id))
        if rem:
            self.SESSION.delete(rem)
            self.SESSION.commit()

    def get_all_users(self):
        self._.__table__.create(checkfirst=True)
        rem = self.SESSION.query(self.Database).all()
        self.SESSION.close()
        self.all_users.clear()
        for i in rem:
            self.all_users.append(i.chat_id)
        return self.all_users

