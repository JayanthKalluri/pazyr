import logging
import queue
from pathlib import Path
from logging.handlers import QueueHandler, QueueListener
from threading import Lock
from ..constants import *

# Global state
_log_queue: queue.Queue = queue.Queue()
_listener: QueueListener | None = None
_initialized: bool = False
_lock = Lock()


def init_logger(level: int = logging.INFO) -> None:
    """
    Initialize global async logging system.
    Must be called once at application startup.
    """
    global _listener, _initialized

    with _lock:
        if _initialized:
            return

        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        # root_logger.propagate = False

        # Prevent duplicate handlers (important in reload/dev)
        if not any(isinstance(h, QueueHandler) for h in root_logger.handlers):
            queue_handler = QueueHandler(_log_queue)
            root_logger.addHandler(queue_handler)

        # Console handler (actual output)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))

        # Listener thread
        _listener = QueueListener(
            _log_queue,
            stream_handler,
            respect_handler_level=True
        )
        _listener.start()

        _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.
    Usage: logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def shutdown_logger() -> None: 
    """
    Gracefully stop the logging listener.
    Call this during application shutdown.
    """
    global _listener, _initialized

    if _listener:
        _listener.stop()
        _listener = None
    
    _initialized = False