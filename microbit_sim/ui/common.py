import curses
import functools
import logging
from collections import namedtuple

import asyncio
import numpy as np
import time
from decorator import decorator

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
BRIGHTNESS = BRIGHTNESS_UNICODE_BLOCK

BRIGHTNESS_8BIT = np.linspace(0, 255, num=10, dtype=int)

CURSES_LED_COLOR_RANGE = (17, 17 + len(BRIGHTNESS_8BIT))

OUTPUT_MAX_LINES = 1000


def ansi_brightness(value):
    return '\x1b[38;2;{red};0;0m'.format(red=BRIGHTNESS_8BIT[value])


def format_brightness(value, char=U_LOWER_HALF_BLOCK):
    return '{}{char}\x1b[0m'.format(
        ansi_brightness(value),
        char=char)


BRIGHTNESS_8BIT_ANSI = [format_brightness(value) for value in range(0, 10)]


class Rect:
    def __init__(self, x=None, y=None, width=None, height=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def __repr__(self):
        return '<Rect x={self.x}, y={self.y}, ' \
               'width={self.width}, height={self.height}>'.format(self=self)

    @property
    def y2(self):
        return self.y + self.height

    @property
    def x2(self):
        return self.x + self.width


def start_curses(hide_cursor=True):
    screen = curses.initscr()

    # What curses.wrapper does
    curses.noecho()
    curses.cbreak()

    # Hide cursor
    curses.curs_set(not hide_cursor)

    # Colors
    curses.start_color()
    curses.use_default_colors()
    init_colors()

    # Set input timeout to speed up .getch()
    screen.timeout(0)
    screen.keypad(True)

    return screen


def end_curses():
    if curses.isendwin():
        _log.warning('Curses already ended')
        return

    #self.screen.keypad(0)
    curses.nocbreak()
    curses.echo()
    curses.endwin()


def end_curses_on_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            end_curses()
            raise

    return wrapper


def pair_for_value(value):
    return curses.color_pair(CURSES_LED_COLOR_RANGE[0] + value)


def init_colors():
    _log.debug('Init colors')
    for color_number, (value, red) in zip(
            range(*CURSES_LED_COLOR_RANGE),
            enumerate(BRIGHTNESS_8BIT)):
        curses.init_color(color_number, int(red / 255 * 1000), 0, 0)
        curses.init_pair(color_number, color_number, -1)

    _log.debug('colors initiated')


Layout = namedtuple('Layout', [
    'screen',
    'microbit',
    'leds',
    'output',
    'stats',
])


def update_layout(screen):
    available_height, available_width = screen.getmaxyx()
    screen = Rect(x=0, y=0, width=available_width, height=available_height)

    leds = Rect(x=4, y=2, width=13, height=7)

    microbit = Rect(x=0, y=0,
                    width=leds.width + leds.x * 2,
                    height=leds.height + leds.y * 2)

    available_height -= microbit.height

    stats = Rect(y=microbit.y2 + available_height - 1, x=0,
                 width=screen.width,
                 height=1)

    available_height -= stats.height

    output = Rect(y=microbit.y2, x=0,
                  width=available_width,
                  height=available_height)

    layout = Layout(screen=screen,
                    microbit=microbit,
                    leds=leds,
                    output=output,
                    stats=stats)
    _log.info('updated layout=%r', layout)
    return layout


Windows = namedtuple('Windows', [
    'leds',
    'output',
    'output_pad',
    'stats'
])


def create_windows(screen, layout):
    microbit = screen.subwin(layout.microbit.height,
                             layout.microbit.width,
                             layout.microbit.y,
                             layout.microbit.x)

    leds = screen.subwin(layout.leds.height,
                         layout.leds.width,
                         layout.leds.y,
                         layout.leds.x)

    output = curses.newwin(layout.output.height,
                           layout.output.width,
                           layout.output.y,
                           layout.output.x)

    output_pad = curses.newpad(OUTPUT_MAX_LINES,
                               layout.output.width - 2)

    stats = screen.subwin(layout.stats.height,
                          layout.stats.width,
                          layout.stats.y,
                          layout.stats.x)

    leds.border()
    leds.refresh()
    microbit.border()
    microbit.refresh()
    output.border()
    output.refresh()

    return Windows(leds=leds,
                   output=output,
                   output_pad=output_pad,
                   stats=stats)


def update_timing_average(t_last, average, smoothing=0.9):
    t_now = time.time()
    t_delta = t_now - t_last

    new_average = ((average * smoothing) +
                   (1 / t_delta * (1.0 - smoothing)))

    return t_now, new_average


class ratelimit:
    def __init__(self, min_delta):
        self.t_last = 0
        self.min_delta = min_delta

    def __aiter__(self):
        return self

    async def __anext__(self):
        t_now = time.time()
        t_delta = t_now - self.t_last

        t_remaining = self.min_delta - t_delta
        if t_remaining > 0:
            await asyncio.sleep(t_remaining)

        self.t_last = t_now
        return t_now


def tail_recursive(coro):
    loop = asyncio.get_event_loop()

    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        result = await coro(*args, **kwargs)
        loop.create_task(coro)

    return wrapper
