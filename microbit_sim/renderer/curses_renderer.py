import io
import logging
import curses
import queue
from collections import defaultdict
from collections import deque, namedtuple
from datetime import datetime

import numpy as np

import sys

import time

from microbit_sim.renderer.abstract import AbstractRenderer
from microbit_sim.renderer.common import U_LOWER_HALF_BLOCK, BRIGHTNESS_8BIT

COUNTER_SMOOTHING = 0.9

_log = logging.getLogger(__name__)

Layout = namedtuple('Layout', [
    'screen',
    'microbit',
    'leds',
    'output',
    'stats',
])


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


class CursesRenderer(AbstractRenderer):
    COLORS_BRIGHTNESS_RANGE = (17, 17 + len(BRIGHTNESS_8BIT))
    MIN_TICK_DELTA = 1 / 1000
    OUTPUT_MAX_LINES = 1000

    def __init__(self):
        self._time_last_tick = 0

        self.output_lines = deque([''], maxlen=self.OUTPUT_MAX_LINES)

        self.layout = None

        # Curses
        self.screen = None
        self.win_leds = None
        self.win_output = None
        self.pad_output = None
        self.win_stats = None

        # Stats
        self._counters_last = {}

        self.counters = defaultdict(lambda: 0)

    def update_timing(self, name):
        t_last = self._counters_last.setdefault(name, 0)
        t_now = time.time()
        t_delta = t_now - t_last
        self._counters_last[name] = t_now

        per_second = 1 / t_delta

        average = self.counters.setdefault(name, 0)

        self.counters[name] = ((average * COUNTER_SMOOTHING) +
                               (per_second * (1.0 - COUNTER_SMOOTHING)))

    def start_curses(self):
        self.screen = curses.initscr()

        # What curses.wrapper does
        curses.noecho()
        curses.cbreak()

        # Hide cursor
        curses.curs_set(0)

        # Colors
        curses.start_color()
        curses.use_default_colors()
        self.init_colors()

        # Layout
        self.update_layout()

        # Windows
        # self.w_microbit = self.screen.subwin(self.layout.microbit.height,
        #                                      self.layout.microbit.width)
        self.win_leds = self.screen.subwin(self.layout.leds.height,
                                           self.layout.leds.width,
                                           self.layout.leds.y,
                                           self.layout.leds.x)
        self.win_output = curses.newwin(self.layout.output.height,
                                        self.layout.output.width,
                                        self.layout.output.y,
                                        self.layout.output.x)

        self.pad_output = curses.newpad(self.OUTPUT_MAX_LINES,
                                        self.layout.output.width - 2)

        self.win_stats = self.screen.subwin(self.layout.stats.height,
                                            self.layout.stats.width,
                                            self.layout.stats.y,
                                            self.layout.stats.x)

        # Set input
        self.screen.timeout(10)
        self.screen.keypad(True)

        self.win_leds.timeout(10)
        self.win_leds.keypad(True)

    def update_layout(self):
        available_height, available_width = self.screen.getmaxyx()
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

        self.layout = Layout(screen=screen,
                             microbit=microbit,
                             leds=leds,
                             output=output,
                             stats=stats)
        _log.info('updated layout=%r', self.layout)

    def run(self, queues):
        self.start_curses()

        while True:
            self.update_timing('mainloop')
            # Rate limiting
            t_now = time.time()
            delta_t = t_now - self._time_last_tick

            if delta_t < self.MIN_TICK_DELTA:
                time.sleep(self.MIN_TICK_DELTA - delta_t)

            self._time_last_tick = t_now

            try:
                control = queues.control.get_nowait()
            except queue.Empty:
                pass
            else:
                if control == 'stop':
                    _log.info('Stopping')
                    break

            try:
                buffer = queues.display.get_nowait()
            except queue.Empty:
                pass
            else:
                self.render_display(buffer)

            try:
                output = queues.output.get_nowait()
            except queue.Empty:
                pass
            else:
                self.add_output(output)

            curses.doupdate()

            self.render_stats()

            self.get_input()

        self.end_curses()

    def render_stats(self):
        self.win_stats.clear()
        self.win_stats.addstr(
            '{datetime}: '
            'render: {counters[render]:.2f}/s, '
            'mainloop: {counters[mainloop]:.2f}/s, '
            'stats: {counters[mainloop]:.2f}/s'
            .format(counters=self.counters,
                    datetime=datetime.now().isoformat(sep=' ')))
        self.win_stats.noutrefresh()

    def add_output(self, output):
        _log.debug('add_output(output=%r)', output)
        lines = output.split('\n')
        first, *rest = lines
        self.output_lines[-1] += first
        self.output_lines.extend(rest)
        self.render_output()

    def render_output(self):
        self.update_timing('output')
        self.win_output.border()

        self.pad_output.clear()
        for i, line in enumerate(self.output_lines):
            self.pad_output.addstr(i + 1, 0, line)

        # self.w_output.refresh()

        pad_min_y = max(
            len(self.output_lines) - self.layout.output.height, 0)
        self.win_output.noutrefresh()
        self.pad_output.noutrefresh(
            pad_min_y,
            0,
            self.layout.output.y + 1,
            self.layout.output.x + 1,
            self.layout.output.y2 - 2,
            self.layout.output.x2 - 1)

    def end_curses(self):
        if curses.isendwin():
            _log.warning('Curses already ended')
            return

        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def init_colors(self):
        _log.debug('Init colors')
        for color_number, (value, red) in zip(
                range(*self.COLORS_BRIGHTNESS_RANGE),
                enumerate(BRIGHTNESS_8BIT)):
            curses.init_color(color_number, int(red / 255 * 1000), 0, 0)
            curses.init_pair(color_number, color_number, -1)

        _log.debug('colors initiated')

    def pair_for_value(self, value):
        return curses.color_pair(self.COLORS_BRIGHTNESS_RANGE[0] + value)

    def get_input(self):
        from microbit import button_a, button_b

        ch = self.win_leds.getch()

        if ch == curses.KEY_LEFT:
            button_a._press()
        elif ch == curses.KEY_RIGHT:
            button_b._press()

    def render_display(self, buffer):
        _log.debug('render_display(buffer=%r)', buffer)
        self.update_timing('render')

        def led_x(x):
            return self.layout.microbit.x + x * 2 + 2

        def led_y(y):
            return self.layout.microbit.y + y + 1

        try:
            self.win_leds.border()
            for (y, x), value in np.ndenumerate(buffer):
                self.win_leds.addch(led_y(y), led_x(x),
                                    U_LOWER_HALF_BLOCK,
                                    self.pair_for_value(value))

            self.win_leds.refresh()
        except Exception:
            self.end_curses()
            raise

    def __del__(self):
        self.end_curses()
