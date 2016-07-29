import importlib
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


RENDERER = get_instance(
    os.environ.get('RENDERER', 'microbit._simulator.renderer:ANSIRenderer'))
