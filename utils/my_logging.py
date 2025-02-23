# -*- coding: utf-8 -*-

import functools
import logging.config
import os

import utils.string_util as su

CFG_DEBUG = "DEBUG"

# Get the project root directory. It is the parent of the current file.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s (%(lineno)d): %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "default_file": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(PROJECT_ROOT, "logs", "app.default.log"),
            "when": "D",
            "encoding": "utf-8",
        },
        "error_file": {
            "level": "ERROR",
            "formatter": "standard",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": os.path.join(PROJECT_ROOT, "logs", "app.error.log"),
            "when": "D",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "default_file", "error_file"],
        "level": "DEBUG",
    },
    "loggers": {
        "urllib3.connectionpool": {
            "level": "INFO",  # Set to INFO or higher to suppress DEBUG logs
            "handlers": ["console", "default_file", "error_file"],
            "propagate": False,  # Prevent the log messages from being handled by the root logger
        },
    },
}


def log_entry_exit(func):
    """
    Decorator for logging entry and exit
    """

    @functools.wraps(func)
    def entry_exit(*args, **kwargs):
        logger = get_logger(func.__module__ + su.DOT + func.__qualname__)

        logger.debug(f"entry arguments:{su.NEW_LINE}{args}, {kwargs}")

        return_values = func(*args, **kwargs)

        logger.debug(f"exit return_values:{su.NEW_LINE}{return_values}")

        return return_values

    return entry_exit


def get_logger(name=None):
    # Create log directory if missing
    os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)

    # Configure logging
    logging.config.dictConfig(DEFAULT_CONFIG)

    # Determine the logger to use
    logger = logging.getLogger(name)

    # Determine the log level
    log_level = logging.DEBUG if os.environ.get("DEBUG") == "true" else logging.INFO

    # Set the log level
    logger.setLevel(log_level)

    return logger
