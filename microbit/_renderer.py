import curses
import io
import sys
import time
from abc import ABCMeta, abstractmethod

import atexit
import numpy as np

U_BLACK_SQUARE = '\u25A0'  # ■ BLACK SQUARE
U_FULL_BLOCK = '\u2588'  # █ FULL BLOCK
U_LOWER_HALF_BLOCK = '\u2584'  # ▄ LOWER HALF BLOCK
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


def ansi_brightness(value):
    return '\x1b[38;2;{red};0;0m'.format(red=BRIGHTNESS_8BIT[value])


def format_brightness(value, char=U_LOWER_HALF_BLOCK):
    return '{}{char}\x1b[0m'.format(
        ansi_brightness(value),
        char=char)


BRIGHTNESS_8BIT_ANSI = [format_brightness(value) for value in range(0, 10)]


class AbstractRenderer(metaclass=ABCMeta):
    @abstractmethod
    def render(self, buffer: np.ndarray) -> None:
        pass


class ANSIRenderer(AbstractRenderer):
    SPACE = ' '  # For clarity
    TOP_LEFT = '\u256d'
    TOP_RIGHT = '\u256e'
    BOTTOM_RIGHT = '\u256f'
    BOTTOM_LEFT = '\u2570'
    LEFT = RIGHT = '\u2502'
    BOTTOM = TOP = '\u2500'
    LED_CHAR = '\u25A0'  # ■ BLACK SQUARE

    MAX_FPS = 60

    MARGIN_X = 7
    MARGIN_Y = 1
    LED_X = 9
    LED_Y = 5
    BORDER_WIDTH = 1

    def __init__(self):
        self.term_buf = sys.stderr
        self._last_render = time.time()

        self.hide_cursor()
        self.write_decoration()

        atexit.register(self.show_cursor)

    def hide_cursor(self):
        self.term_buf.write('\x1b[?25l')

    def show_cursor(self):
        self.term_buf.write('\x1b[?12;25h')

    def center(self, text, length=None):
        if length is None:
            return text

        x_pad, remainder = divmod(length - len(text), 2)
        return (self.SPACE * (x_pad + remainder) +
                text +
                self.SPACE * x_pad)

    def pad_x(self, text, corr_l=0, corr_r=0):
        pad_l = self.SPACE * (self.MARGIN_X + corr_l)
        pad_r = self.SPACE * (self.MARGIN_X + corr_r)

        return '{left}{pad_l}{text}{pad_r}{right}\n'.format(
            pad_l=pad_l,
            text=text,
            pad_r=pad_r,
            left=self.LEFT,
            right=self.RIGHT
        )

    def write_decoration(self):
        buf = io.StringIO()

        # Write top border
        buf.write(self.TOP_LEFT + self.TOP * (self.MARGIN_X * 2 + self.LED_X) +
                  self.TOP_RIGHT + '\n')

        # Empty lines for Y margins
        y_pad = [self.pad_x(self.SPACE * self.LED_X)
                 for _ in range(0, self.MARGIN_Y)]

        # Header and
        buf.write(self.pad_x(self.center('microbit', self.LED_X)))
        buf.write(''.join(y_pad[:-1]))

        # Empty area for LED indicators
        for i in range(0, self.LED_Y):
            buf.write(self.pad_x(self.SPACE * self.LED_X))

        buf.write(''.join(y_pad))

        buf.write(self.BOTTOM_LEFT +
                  self.BOTTOM * (self.MARGIN_X * 2 + self.LED_X) +
                  self.BOTTOM_RIGHT + '\n')
        buf.flush()

        self.term_buf.write('\x1b[2J'
                            '\x1b[1;1H')
        self.term_buf.write(buf.getvalue())
        self.term_buf.flush()

    def render(self, buffer):
        # Rate limiting
        t_now = time.time()
        delta_t = t_now - self._last_render

        if delta_t < 1 / 60:
            return

        self._last_render = t_now

        buf = io.StringIO()

        for y, line in enumerate(buffer):
            for x, value in enumerate(line):
                ansi_x = self.MARGIN_X + x * 2 + self.BORDER_WIDTH + 1
                ansi_y = self.MARGIN_Y + y + self.BORDER_WIDTH + 1
                buf.write('\x1b[{y};{x}H'.format(x=ansi_x, y=ansi_y))
                buf.write(format_brightness(value))
                # buf.write(
                #     self.pad_x(
                #         ''.join(' {}'.format(
                #             format_brightness(value, self.LED_CHAR)) for
                # value in line),
                #         corr_l=-1))

        buf.flush()
        self.term_buf.write(buf.getvalue())
        self.term_buf.flush()


class CursesRenderer(AbstractRenderer):
    def __init__(self):
        self._screen = curses.initscr()

        curses.start_color()
        curses.use_default_colors()

    def render(self, buffer):
        try:
            self._screen.clear()
            for (x, y), value in np.ndenumerate(buffer):
                self._screen.addch(y, x, BRIGHTNESS[value])

            self._screen.refresh()
        except Exception:
            self._deinit()
            raise

    def _deinit(self):
        curses.endwin()
