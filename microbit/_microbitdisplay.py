from typing import Iterable

import numpy as np

from microbit._renderer import CursesRenderer, ANSIRenderer


class MicroBitDisplay:
    def __init__(self, renderer=None):
        if renderer is None:
            renderer = ANSIRenderer()

        self._renderer = renderer

        self._buffer = np.zeros((5, 5), dtype=np.int8)
        super().__init__()
        self._on = True

    def on(self):
        self._on = True

    def off(self):
        self._on = True

    def is_on(self):
        return self._on

    def get_pixel(self, x, y):
        return self._buffer[x, y]

    def set_pixel(self, x, y, value):
        assert 0 <= value < 10
        self._buffer[x, y] = value
        self._renderer.render(self._buffer)

    def clear(self):
        self._buffer = np.empty((5, 5), dtype=np.int8)
        self._renderer.render()

    def scroll(self, string, delay=150, wait=True, loop=False,
               monospace=False):
        pass

    def show(self, *args, **kwargs):
        def show_image(image):
            pass

        def show_iterable(iterable, delay=400, wait=True, loop=False,
                          clear=False):
            pass

        first_arg = args[0]
        if isinstance(first_arg, Iterable):
            show_iterable(*args, **kwargs)
        elif isinstance(first_arg, Image):
            show_image(first_arg)

    def __del__(self):
        if hasattr(self, '_deinit'):
            self._deinit()


