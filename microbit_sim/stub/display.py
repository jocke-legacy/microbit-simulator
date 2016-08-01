import functools
import logging
from typing import Iterable

import numpy as np
from microbit_sim.stub.base import ImageData
from microbit_sim.stub.image import Image

_log = logging.getLogger(__name__)


def updates(func):
    """
    Helper to render the display after the function has been
    executed.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        #_log.error('updates: func=%r', func)
        if callable(self._update_callback):
            self._update_callback(self._buffer.copy())
        return result

    return wrapper


class Display(ImageData):
    def __init__(self, update_callback, pixel_update_callback):
        self._update_callback = update_callback
        self._pixel_update_callback = pixel_update_callback

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
        self._pixel_update_callback(x, y, value)
        return super(Display, self).set_pixel(x, y, value)

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
