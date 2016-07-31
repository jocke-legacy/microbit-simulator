import importlib
import logging
import os
from typing import Any


def import_object(path: str) -> Any:
    """
    Import an object from a module.

    Example:

    >>> # Import the ``baz`` object from the ``foo.bar`` module.
    >>> import_object('foo.bar:baz')
    """
    module_path, object_name = path.split(':')
    module = importlib.import_module(module_path)

    return getattr(module, object_name)


def get_instance(path, *args, **kwargs):
    type_ = import_object(path)
    return type_(*args, **kwargs)


def env_int(key: str, default: int) -> int:
    value_str = os.environ.get(key)

    if value_str is not None:
        return int(value_str)

    return default


RENDERER = os.environ.get(
    'RENDERER',
    'microbit_sim.renderer:CursesRenderer')

# Output/Input
ZMQ_STDERR_SOCKET = 'inproc://stderr'
ZMQ_STDOUT_SOCKET = 'inproc://stdout'

# Logging
LOGGING_LEVEL = env_int('LOG_LEVEL', logging.INFO)
LOGGING_PUB_SOCKET = 'ipc:///tmp/microbit-logging.sock'

DISPLAY_QUEUE_SIZE = 1

DISPLAY_SOCKET = 'ipc:///tmp/microbit-display.sock'
CONTROL_SOCKET = 'ipc:///tmp/microbit-control.sock'
