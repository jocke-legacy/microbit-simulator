import logging
import select
import curses
import io
import re
import sys
import time
import tty
from abc import ABCMeta, abstractmethod

import atexit
from contextlib import contextmanager

import numpy as np
import termios

_log = logging.getLogger(__name__)

U_BLACK_SQUARE = '\u25A0'  # ■ BLACK SQUARE
U_FULL_BLOCK = '\u2588'  # █ FULL BLOCK
U_LOWER_HALF_BLOCK = '\u2584'  # ▄ LOWER HALF BLOCK
BRIGHTNESS_UNICODE_BLOCK = [
    ' ',  # 0
    '▁',  # 1
    '▁',  # 2  (duplicate of 1)
    '▂',  # 3
    '▃',  # 4
    '▄',  # 5
    '▅',  # 6
    '▆',  # 7
    '▉',  # 8
    '█',  # 9
]
BRIGHTNESS_8BIT = np.linspace(0, 255, num=10, dtype=int)
BRIGHTNESS = BRIGHTNESS_UNICODE_BLOCK


def ansi_brightness(value):
    return '\x1b[38;2;{red};0;0m'.format(red=BRIGHTNESS_8BIT[value])


def format_brightness(value, char=U_LOWER_HALF_BLOCK):
    return '{}{char}\x1b[0m'.format(
        ansi_brightness(value),
        char=char)


def get_position():
    previous_settings = tty.tcgetattr(sys.stdin.fileno())

    stdin_data = ''
    timeout = 0.5

    variants = set()

    sys.stdout.write('\x1b[6n')
    sys.stdout.flush()

    try:
        tty.setraw(sys.stdin.fileno())

        while True:
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                stdin_data += sys.stdin.read(1)
                _log.debug('Got data: %r', stdin_data)
            else:
                _log.debug('No data.')

            _log.debug('stdin_data=%r', stdin_data)
            variants.add(stdin_data)
            _log.debug('variants=%r', variants)

            if stdin_data and stdin_data[-1] == 'R':
                break
    finally:
        tty.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, previous_settings)

    _log.debug('stdin_data=%r', stdin_data)
    match = re.search(r'\[(?P<y>\d+);(?P<x>\d+)R', stdin_data)

    if match is not None:
        return int(match.group('x')), int(match.group('y'))


@contextmanager
def save_and_restore_cursor(buf):
    buf.write('\x1b[s')
    yield
    buf.write('\x1b[u')


BRIGHTNESS_8BIT_ANSI = [format_brightness(value) for value in range(0, 10)]


class AbstractRenderer(metaclass=ABCMeta):
    @abstractmethod
    def render_leds(self, buffer: np.ndarray) -> None:
        pass


class ANSIRenderer(AbstractRenderer):
    """
    Renders the microbit display using raw ANSI escape codes.

    See https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_codes
    """
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

        #self.START_X, self.START_Y = get_position()

        self.write_decoration()
        # self.hide_cursor()
        #
        # atexit.register(self.show_cursor)

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
        buf.write('\x1b[s')

        for i in range(0, self.LED_Y):
            buf.write(self.pad_x(self.SPACE * self.LED_X))

        buf.write(''.join(y_pad))

        buf.write(self.BOTTOM_LEFT +
                  self.BOTTOM * (self.MARGIN_X * 2 + self.LED_X) +
                  self.BOTTOM_RIGHT + '\n')
        buf.flush()

        # self.term_buf.write('\x1b[2J'
        #                     '\x1b[1;1H')
        self.term_buf.write(buf.getvalue())
        self.term_buf.flush()

    def render_buttons(self, button_a, button_b):
        if button_a._presses:
            pass
        if button_b._presses:
            pass

    def str_at(self, x, y, string, buf=None):
        if buf is None:
            buf = self.term_buf

        ansi_x = x + 1
        ansi_y = y + 1

        # with save_and_restore_cursor(buf):
        buf.write('\x1b[u')

        jump_abs = '\x1b[{y};{x}H'.format(x=ansi_x, y=ansi_y)
        jump_rel = '\x1b[{y}A\x1b[{x}C'.format(
            y=y,
            x=x * 2
        )
        buf.write('{jump}{string}'.format(
            jump=jump_abs,
            string=string,
        ))

    @contextmanager
    def buffer_term(self):
        """
        Hold terminal writes.
        """
        # Replace self.term_buf with a dummy buffer
        real_term = self.term_buf
        self.term_buf = mock_buf = io.StringIO()
        yield
        # Put the real term_buf back and write the contents of the dummy
        # buffer to it
        real_term.write(self.term_buf.getvalue())
        real_term.flush()
        self.term_buf = real_term

    def render_leds(self, buffer):
        time.sleep(0.1)
        # Rate limiting
        t_now = time.time()
        delta_t = t_now - self._last_render

        if delta_t < 1 / 60:
            return

        self._last_render = t_now

        with self.buffer_term():
            for y, line in enumerate(buffer):
                for x, value in enumerate(line):
                    _x = self.MARGIN_X + x * 2 + self.BORDER_WIDTH
                    _y = self.MARGIN_Y + y + self.BORDER_WIDTH

                    self.str_at(x, y, format_brightness(value))

        self.term_buf.flush()


class CursesRenderer(AbstractRenderer):
    def __init__(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        curses.curs_set(0)

        self.microbit = curses.newwin(10, 20)
        self.win = curses.newwin(7, 13, 5, 5)

    def render_leds(self, buffer):
        from microbit import button_a, button_b
        self.win.nodelay(True)
        ch = self.win.getch()

        if ch == curses.KEY_LEFT:
            button_a._press()
        elif ch == curses.KEY_RIGHT:
            button_b._press()

        def led_x(x):
            return x * 2 + 2

        def led_y(y):
            return y + 1

        try:
            self.win.border()
            self.win.attron(curses.color_pair(1))
            self.win.attron(curses.A_BOLD)
            for (x, y), value in np.ndenumerate(buffer):
                # sys.stderr.write(ansi_brightness(value))
                # sys.stderr.flush()
                #self.win.addch(y, x * 2, U_LOWER_HALF_BLOCK)
                self.win.addch(led_y(y), led_x(x),
                               BRIGHTNESS_UNICODE_BLOCK[value])

            self.win.attroff(curses.color_pair(1))
            self.win.attroff(curses.A_BOLD)

            self.win.refresh()
            self.screen.refresh()
        except Exception:
            self._deinit()
            raise

    def _deinit(self):
        curses.endwin()

    def __del__(self):
        self._deinit()

