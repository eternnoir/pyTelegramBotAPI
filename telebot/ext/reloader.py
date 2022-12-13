
from watchdog.events import FileSystemEventHandler
from watchdog.events import FileSystemEvent
import psutil
import os
import sys
import logging

logger = logging.getLogger('TeleBot')

class EventHandler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        logger.info('* Detected changes in: %s, reloading', (event.src_path))
        restart_file()

def restart_file():
    try:
        p = psutil.Process(os.getpid())
        for handler in p.open_files() + p.connections():
            os.close(handler.fd)
    except OSError:
        pass
    except Exception as e:
        logger.error(e)

    python = sys.executable
    
    if os.name == 'nt':
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        os.execl(python, python, *sys.argv)
