import io
import logging
import curses
import queue
from collections import deque

import numpy as np

import sys

import time

from ..base import Queues

from .abstract import AbstractRenderer
from .common import U_LOWER_HALF_BLOCK, BRIGHTNESS_8BIT

_log = logging.getLogger(__name__)


class Rect:
    def __init__(self, x=None, y=None, width=None, height=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

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

    def __init__(self, queues: Queues):
        self.queues = queues

        self._time_last_tick = 0

        self.output_lines = deque([''], maxlen=self.OUTPUT_MAX_LINES)

        # Curses
        self.screen = None
        self.layout = None
        self.w_output = None
        self.w_leds = None
        self._curses_ended = False

    def start_curses(self):
        self._curses_ended = False
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
        self.w_microbit = self.screen.subwin(self.layout.microbit.height,
                                             self.layout.microbit.width)
        self.w_leds = self.screen.subwin(self.layout.microbit.leds.height,
                                             self.layout.microbit.leds.height,
                                             self.layout.microbit.leds.y,
                                             self.layout.microbit.leds.x)
        self.w_output = self.screen.subpad(self.OUTPUT_MAX_LINES,
                                           self.layout.output.width,
                                           self.layout.output.y,
                                           self.layout.output.x)

        # Set input
        self.screen.timeout(10)
        self.screen.keypad(True)

        self.w_leds.timeout(10)
        self.w_leds.keypad(True)

    def update_layout(self):
        rest_y, rest_x = self.screen.getmaxyx()
        layout = Rect(x=0, y=0, width=rest_x, height=rest_y)

        leds = Box(x=4, y=2, width=13, height=7)

        microbit = Rect(x=0, y=0,
                        width=leds.width + leds.x * 2,
                        height=leds.height + leds.y * 2)
        setattr(microbit, 'leds', leds)
        setattr(layout, 'microbit', microbit)

        rest_y -= microbit.height

        output = Rect(y=microbit.y2, x=0,
                      width=rest_x,
                      height=rest_y)
        setattr(layout, 'output', output)
        self.layout = layout

    def run(self):
        self.start_curses()

        while True:
            # Rate limiting
            t_now = time.time()
            delta_t = t_now - self._time_last_tick

            if delta_t < self.MIN_TICK_DELTA:
                time.sleep(self.MIN_TICK_DELTA - delta_t)

            self._time_last_tick = t_now

            try:
                control = self.queues.control.get_nowait()
            except queue.Empty:
                pass
            else:
                if control == 'stop':
                    _log.info('Stopping')
                    break

            try:
                buffer = self.queues.display.get_nowait()
            except queue.Empty:
                pass
            else:
                self.render_display(buffer)

            try:
                output = self.queues.output.get_nowait()
            except queue.Empty:
                pass
            else:
                self.add_output(output)

        self.end_curses()

    def add_output(self, output):
        lines = output.split('\n')
        first, *rest = lines
        self.output_lines[-1] += first
        self.output_lines.extend(rest)
        self.render_output()

    def render_output(self):
        num_lines = self.layout.output.height
        self.w_output.clear()
        for line in self.output_lines[-num_lines:]:
            self.w_output.addstr(line)

        self.w_output.refresh([
            0,
            0,
            self.layout.output.y,
            self.layout.output.x,
            self.layout.output.y2,
            self.layout.output.x2])

    def end_curses(self):
        if self._curses_ended:
            _log.warning('Curses already ended')
            return

        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        #sys.stdout = sys.__stdout__
        #sys.stdout.write(self.stdout.getvalue())

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

    # def run_logging_renderer(self):
    #     while True:
    #         self.render_logging_tick()
    #         time.sleep(0.001)
    #
    # def render_logging_tick(self):
    #     for message in self.logging_data.messages:
    #         try:
    #             self.log_win.addstr(str(message) + '\n')
    #         except:
    #             pass
    #
    #     self.log_win.refresh()

    def get_input(self):
        pass

    def render_display(self, buffer):
        from microbit import button_a, button_b
        self.render_output()

        ch = self.w_leds.getch()

        if ch == curses.KEY_LEFT:
            button_a._press()
        elif ch == curses.KEY_RIGHT:
            button_b._press()

        def led_x(x):
            return x * 2 + 2

        def led_y(y):
            return y + 1

        try:
            self.w_leds.border()
            for (y, x), value in np.ndenumerate(buffer):
                self.w_leds.addch(led_y(y), led_x(x),
                                  U_LOWER_HALF_BLOCK,
                                  self.pair_for_value(value))

            self.w_leds.refresh()
        except Exception:
            self.end_curses()
            raise

    def __del__(self):
        self.end_curses()
