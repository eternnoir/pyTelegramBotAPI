# -*- coding: utf-8 -*-

import threading
from six import string_types

# Python3 queue support.
try:
    import Queue
except ImportError:
    import queue as Queue


class ThreadPool:
    class WorkerThread(threading.Thread):
        count = 0

        def __init__(self, queue):
            threading.Thread.__init__(self, name="WorkerThread{0}".format(self.__class__.count + 1))
            self.__class__.count += 1
            self.queue = queue
            self.daemon = True

            self._running = True
            self.start()

        def run(self):
            while self._running:
                try:
                    task, args, kwargs = self.queue.get(block=True, timeout=.01)
                    task(*args, **kwargs)
                except Queue.Empty:
                    pass

        def stop(self):
            self._running = False

    def __init__(self, num_threads=4):
        self.tasks = Queue.Queue()
        self.workers = [self.WorkerThread(self.tasks) for _ in range(num_threads)]

        self.num_threads = num_threads

    def put(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def close(self):
        for worker in self.workers:
            worker.stop()
        for worker in self.workers:
            worker.join()

class AsyncTask:
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.done = False
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.result = e
        self.done = True

    def wait(self):
        if not self.done:
            self.thread.join()
        if isinstance(self.result, Exception):
            raise self.result
        else:
            return self.result


def async():
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return AsyncTask(fn, *args, **kwargs)

        return wrapper

    return decorator


def is_string(var):
    return isinstance(var, string_types)

def is_command(text):
    """
    Checks if `text` is a command. Telegram chat commands start with the '/' character.
    :param text: Text to check.
    :return: True if `text` is a command, else False.
    """
    return text.startswith('/')


def extract_command(text):
    """
    Extracts the command from `text` (minus the '/') if `text` is a command (see is_command).
    If `text` is not a command, this function returns None.

    Examples:
    extract_command('/help'): 'help'
    extract_command('/help@BotName'): 'help'
    extract_command('/search black eyed peas'): 'search'
    extract_command('Good day to you'): None

    :param text: String to extract the command from
    :return: the command if `text` is a command (according to is_command), else None.
    """
    return text.split()[0].split('@')[0][1:] if is_command(text) else None


def split_string(text, chars_per_string):
    """
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.

    :param text: The text to split
    :param chars_per_string: The number of characters per line the text is split into.
    :return: The splitted text as a list of strings.
    """
    return [text[i:i + chars_per_string] for i in range(0, len(text), chars_per_string)]
