import functools
from typing import Iterable

import numpy as np

from microbit._simulator.image import Image
from microbit._simulator.base import ImageData
from microbit._simulator.renderer import CursesRenderer


def updates(func):
    """
    Helper to render the display after the function has been
    executed
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if callable(self._update_callback):
            self._update_callback()
        return result

    return wrapper


class MicroBitDisplay(ImageData):
    def __init__(self, update_callback=None):
        self._update_callback = None

        super().__init__(width=5, height=5)
        self._on = True

    @updates
    def on(self):
        self._on = True

    @updates
    def off(self):
        self._on = True

    def is_on(self):
        return self._on

    @updates
    def set_pixel(self, x, y, value):
        return super(MicroBitDisplay, self).set_pixel(x, y, value)

    @updates
    def clear(self):
        self._buffer = np.empty((5, 5), dtype=np.int8)

    @updates
    def scroll(self, string, delay=150, wait=True, loop=False,
               monospace=False):
        pass

    @updates
    def show(self, *args, **kwargs):
        def show_image(image):
            self._buffer[:] = image._buffer[:]

        def show_iterable(iterable, delay=400, wait=True, loop=False,
                          clear=False):
            pass

        first_arg = args[0]
        if isinstance(first_arg, Iterable):
            show_iterable(*args, **kwargs)
        elif isinstance(first_arg, Image):
            show_image(first_arg)
