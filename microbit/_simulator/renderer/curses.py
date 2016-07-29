import io
import logging
import curses
import threading

import numpy as np

import sys

from .abstract import AbstractRenderer
from .common import U_LOWER_HALF_BLOCK, BRIGHTNESS_8BIT

_log = logging.getLogger(__name__)


class CursesRenderer(AbstractRenderer):
    COLORS_BRIGHTNESS_RANGE = (17, 17 + len(BRIGHTNESS_8BIT))

    def __init__(self):
        self.stdout = io.StringIO()
        sys.stdout = self.stdout

        self.screen = curses.initscr()

        # Sensible stuff
        curses.noecho()
        curses.cbreak()

        # Hide cursor
        curses.curs_set(0)

        # Colors
        curses.start_color()
        curses.use_default_colors()
        self.init_colors()

        # Windows
        self.w_microbit = self.screen.subwin(10, 20)
        self.w_leds = self.screen.subwin(7, 13, 0, 0)
        self.w_output = self.screen.subpad(50, 0)

        # Set input
        self.screen.timeout(10)
        self.screen.keypad(True)

        self.w_leds.timeout(10)
        self.w_leds.keypad(True)

        # self.logging_data = logging_data
        # self.log_win = curses.newwin(40, 40, 0, 13)

        # self.t_logging = threading.Thread(target=self.run_logging_renderer)
        # self.t_logging.start()

    def end_curses(self):
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        sys.stdout = sys.__stdout__
        sys.stdout.write(self.stdout.getvalue())

    def init_colors(self):
        _log.debug('Init colors')
        for color_number, (value, red) in zip(
                range(*self.COLORS_BRIGHTNESS_RANGE),
                enumerate(BRIGHTNESS_8BIT)):
            curses.init_color(color_number, int(red / 255 * 1000), 0, 0)
            curses.init_pair(color_number, color_number, -1)
            #curses.

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

    def render_output(self):
        max_y, max_x = self.screen.getmaxyx()
        self.w_output.addstr(self.stdout.getvalue())
        self.w_output.refresh([])

    def render_display(self, display):
        buffer = display._buffer
        from microbit import button_a, button_b
        #self.win.nodelay(True)
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
            #self.win.attron(curses.A_BOLD)
            for (x, y), value in np.ndenumerate(buffer):
                # sys.stderr.write(ansi_brightness(value))
                # sys.stderr.flush()
                #self.win.addch(y, x * 2, U_LOWER_HALF_BLOCK)
                self.w_leds.addch(led_y(y), led_x(x),
                                  U_LOWER_HALF_BLOCK,
                                  self.pair_for_value(value))

            #self.win.attroff(curses.A_BOLD)

            self.w_leds.refresh()
            #self.screen.refresh()
        except Exception:
            self.end_curses()
            raise

    def __del__(self):
        self.end_curses()
