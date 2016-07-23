import sys
import io
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
    SPACE = ' '  # For clarity
    TOP_LEFT = '\u256d'
    TOP_RIGHT = '\u256e'
    BOTTOM_RIGHT = '\u256f'
    BOTTOM_LEFT = '\u2570'
    LEFT = RIGHT= '\u2502'
    BOTTOM = TOP = '\u2500'
    LED = '\u25A0'  # ■ BLACK SQUARE

    def _render(self):
        sys.stdout.write('\033[2J\033[1;1H')

        border = 1
        led = 9
        margin_x = 7
        margin_y = 1

        def pad_x(text, corr_l=0, corr_r=0):
            pad_l = self.SPACE * (margin_x + corr_l)
            pad_r = self.SPACE * (margin_x + corr_r)

            return '{left}{pad_l}{text}{pad_r}{right}\n'.format(
                pad_l=pad_l,
                text=text,
                pad_r=pad_r,
                left=self.LEFT,
                right=self.RIGHT
            )

        def format_brightness(value):
            return '\x1b[38;2;{red};0;0m{char}\x1b[0m'.format(
                red=BRIGHTNESS_8BIT[value],
                char=self.LED)

        def center(text, length=None):
            if length is None:
                return text

            x_pad, remainder = divmod(length - len(text), 2)
            return (self.SPACE * (x_pad + remainder) +
                    text +
                    self.SPACE * x_pad)

        def left(text, length=None):
            if length is None:
                return text

        buf = io.StringIO()

        buf.write(self.TOP_LEFT + self.TOP * (margin_x * 2 + led) +
                  self.TOP_RIGHT + '\n')
        y_pad = [pad_x(self.SPACE * led) for _ in range(0, margin_y)]

        buf.write(pad_x(center('microbit', led)))
        buf.write(''.join(y_pad[:-1]))

        for y, line in enumerate(self._buffer):
            buf.write(pad_x(''.join(' {}'.format(format_brightness(value))
                                    for value in line),
                            corr_l=-1))

        buf.write(''.join(y_pad))

        buf.write(self.BOTTOM_LEFT + self.BOTTOM * (margin_x * 2 + led) +
                  self.BOTTOM_RIGHT + '\n')
        buf.flush()

        sys.stdout.write(buf.getvalue())
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


