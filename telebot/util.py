# -*- coding: utf-8 -*-

import threading
import re
import sys
import six
from six import string_types

# Python3 queue support.

try:
    import Queue
except ImportError:
    import queue as Queue

from telebot import logger


class WorkerThread(threading.Thread):
        count = 0

        def __init__(self, exception_callback=None, queue=None, name=None):
            if not name:
                name = "WorkerThread{0}".format(self.__class__.count + 1)
                self.__class__.count += 1
            if not queue:
                queue = Queue.Queue()

            threading.Thread.__init__(self, name=name)
            self.queue = queue
            self.daemon = True

            self.received_task_event = threading.Event()
            self.done_event = threading.Event()
            self.exception_event = threading.Event()
            self.continue_event = threading.Event()

            self.exception_callback = exception_callback
            self.exc_info = None
            self._running = True
            self.start()

        def run(self):
            while self._running:
                try:
                    task, args, kwargs = self.queue.get(block=True, timeout=.5)
                    self.continue_event.clear()
                    self.received_task_event.clear()
                    self.done_event.clear()
                    self.exception_event.clear()
                    logger.debug("Received task")
                    self.received_task_event.set()

                    task(*args, **kwargs)
                    logger.debug("Task complete")
                    self.done_event.set()
                except Queue.Empty:
                    pass
                except:
                    logger.debug("Exception occurred")
                    self.exc_info = sys.exc_info()
                    self.exception_event.set()

                    if self.exception_callback:
                        self.exception_callback(self, self.exc_info)
                    self.continue_event.wait()

        def put(self, task, *args, **kwargs):
            self.queue.put((task, args, kwargs))

        def raise_exceptions(self):
            if self.exception_event.is_set():
                six.reraise(self.exc_info[0], self.exc_info[1], self.exc_info[2])

        def clear_exceptions(self):
            self.exception_event.clear()
            self.continue_event.set()

        def stop(self):
            self._running = False


class ThreadPool:

    def __init__(self, num_threads=2):
        self.tasks = Queue.Queue()
        self.workers = [WorkerThread(self.on_exception, self.tasks) for _ in range(num_threads)]
        self.num_threads = num_threads

        self.exception_event = threading.Event()
        self.exc_info = None

    def put(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def on_exception(self, worker_thread, exc_info):
        self.exc_info = exc_info
        self.exception_event.set()
        worker_thread.continue_event.set()

    def raise_exceptions(self):
        if self.exception_event.is_set():
            six.reraise(self.exc_info[0], self.exc_info[1], self.exc_info[2])

    def clear_exceptions(self):
        self.exception_event.clear()

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
        except:
            self.result = sys.exc_info()
        self.done = True

    def wait(self):
        if not self.done:
            self.thread.join()
        if isinstance(self.result, BaseException):
            six.reraise(self.result[0], self.result[1], self.result[2])
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

# CREDITS TO http://stackoverflow.com/questions/12317940#answer-12320352
def or_set(self):
    self._set()
    self.changed()


def or_clear(self):
    self._clear()
    self.changed()


def orify(e, changed_callback):
    e._set = e.set
    e._clear = e.clear
    e.changed = changed_callback
    e.set = lambda: or_set(e)
    e.clear = lambda: or_clear(e)

def OrEvent(*events):
    or_event = threading.Event()
    def changed():
        bools = [e.is_set() for e in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()

    def busy_wait():
        while not or_event.is_set():
            or_event._wait(3)

    for e in events:
        orify(e, changed)
    or_event._wait = or_event.wait
    or_event.wait = busy_wait
    changed()
    return or_event

def extract_arguments(text):
    """
    Returns the argument after the command.
    
    Examples:
    extract_arguments("/get name"): 'name'
    extract_arguments("/get"): ''
    extract_arguments("/get@botName name"): 'name'
    
    :param text: String to extract the arguments from a command
    :return: the arguments if `text` is a command (according to is_command), else None.
    """
    regexp = re.compile("\/\w*(@\w*)*\s*([\s\S]*)",re.IGNORECASE)
    result = regexp.match(text)
    return result.group(2) if is_command(text) else None
