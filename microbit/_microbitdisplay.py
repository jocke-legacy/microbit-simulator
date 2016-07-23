from typing import Iterable

import numpy as np

import curses


class MicroBitDisplay:
    def __init__(self, curses_screen=None):
        self._buffer = np.zeros((5, 5), dtype=np.int8)
        self._screen = None
        self._on = True
        curses.wrapper(self._init_screen)

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
        self._update()

    def clear(self):
        self._buffer = np.empty((5, 5), dtype=np.int8)

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

    def _init_screen(self, curses_screen=None):
        if curses_screen is None:
            curses_screen = curses.initscr()

        self._screen = curses_screen

        curses.start_color()
        curses.use_default_colors()

        # print(curses.can_change_color())
        #
        # if curses.can_change_color():
        #     for i, red in enumerate(BRIGHTNESS):
        #         curses.init_color(126 + i, red, 0, 0)

    def _update(self):
        try:
            self._screen.clear()
            for (x, y), value in np.ndenumerate(self._buffer):
                self._render_pixel(x, y, value)

            self._screen.refresh()
        except Exception:
            self._deinit()
            raise

    def _render_pixel(self, x, y, value):
        char = '\u25A0'  # ■ BLACK SQUARE
        # text = '\x1b[38;2;{red};0;0m{char}\x1b[0m'.format(
        #     red=RED_MAP[value],
        #     char=char)
        # text = str(value)

        self._screen.addch(y, x, BRIGHTNESS[value])

    def _deinit(self):
        curses.endwin()

    def __del__(self):
        self._deinit()

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

BRIGHTNESS = BRIGHTNESS_UNICODE_BLOCK


BRIGHTNESS_8BIT = np.linspace(0, 255, num=10, dtype=int)
