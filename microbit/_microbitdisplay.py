import sys
from typing import Iterable

import numpy as np

import curses

BRIGHTNESS_UNICODE_BLOCK = [
    ' ',  # 0
    '▁',
    '▂',
    '▃',
    '▄',  # 4
    '▅',
    '▆',
    '▉',
    '█',
    '▇',  # 9
]

BRIGHTNESS_8BIT = np.linspace(0, 255, num=10, dtype=int)

BRIGHTNESS = BRIGHTNESS_UNICODE_BLOCK


class ANSIRenderer:
    def _render(self):
        sys.stdout.write('\033[2J\033[1;1H')
        char = '\u25A0'  # ■ BLACK SQUARE

        for y, line in enumerate(self._buffer):
            for x, value in enumerate(line):
                text = '\x1b[38;2;{red};0;0m{char}\x1b[0m'.format(
                    red=BRIGHTNESS_8BIT[value],
                    char=char)

                sys.stdout.write(text)

            sys.stdout.write('\n')

        sys.stdout.flush()


class CursesRenderer:
    def __init__(self):
        self._screen = curses.initscr()

        curses.start_color()
        curses.use_default_colors()

    def _render(self):
        try:
            self._screen.clear()
            for (x, y), value in np.ndenumerate(self._buffer):
                self._render_pixel(x, y, value)

            self._screen.refresh()
        except Exception:
            self._deinit()
            raise

    def _render_pixel(self, x, y, value):

        # text = str(value)

        self._screen.addch(y, x, BRIGHTNESS[value])

    def _deinit(self):
        curses.endwin()


class MicroBitDisplay(ANSIRenderer):
    def __init__(self, curses_screen=None):
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
        self._render()

    def clear(self):
        self._buffer = np.empty((5, 5), dtype=np.int8)
        self._render()

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


