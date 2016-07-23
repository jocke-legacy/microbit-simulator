from typing import Iterable

import numpy as np

import curses


class MicroBitDisplay:
    def __init__(self, curses_screen=None):
        self._buffer = np.empty((5, 5), dtype=int)

        if curses_screen is None:
            curses_screen = curses.initscr()
            curses.start_color()

        self._screen = curses_screen

    def on(self):
        global _display_on
        _display_on = True

    def off(self):
        global _display_on
        _display_on = False

    def is_on(self):
        return _display_on

    def get_pixel(self, x, y):
        return self._buffer[y, x]

    def set_pixel(self, x, y, value):
        self._buffer[y, x] = value
        self._update()

    def clear(self):
        self._buffer = np.empty((5, 5), dtype=int)

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

    def _update(self):
        for (x, y), value in np.ndenumerate(self._buffer):
            self._screen.addstr(x, y, '\u25A0')

        self._screen.refresh()

    def __del__(self):
        curses.endwin()
