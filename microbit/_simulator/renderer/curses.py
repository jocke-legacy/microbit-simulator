import logging
import curses
import threading

import numpy as np
import time

from .abstract import AbstractRenderer
from .common import U_LOWER_HALF_BLOCK, BRIGHTNESS_8BIT

_log = logging.getLogger(__name__)


class CursesRenderer(AbstractRenderer):
    COLORS_BRIGHTNESS_RANGE = (17, 17 + len(BRIGHTNESS_8BIT))

    def __init__(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        self.init_colors()

        # Hide cursor
        curses.curs_set(0)

        self.microbit = curses.newwin(10, 20)
        self.win = curses.newwin(7, 13, 0, 0)

        # self.logging_data = logging_data
        # self.log_win = curses.newwin(40, 40, 0, 13)

        # self.t_logging = threading.Thread(target=self.run_logging_renderer)
        # self.t_logging.start()

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

    def render_display(self, display):
        buffer = display._buffer
        #from microbit import button_a, button_b
        #self.win.nodelay(True)
        #ch = self.win.getch()

        # if ch == curses.KEY_LEFT:
        #     button_a._press()
        # elif ch == curses.KEY_RIGHT:
        #     button_b._press()

        def led_x(x):
            return x * 2 + 2

        def led_y(y):
            return y + 1

        try:
            self.win.border()
            #self.win.attron(curses.A_BOLD)
            for (x, y), value in np.ndenumerate(buffer):
                # sys.stderr.write(ansi_brightness(value))
                # sys.stderr.flush()
                #self.win.addch(y, x * 2, U_LOWER_HALF_BLOCK)
                self.win.addch(led_y(y), led_x(x),
                               U_LOWER_HALF_BLOCK,
                               self.pair_for_value(value))

            #self.win.attroff(curses.A_BOLD)

            self.win.refresh()
            #self.screen.refresh()
        except Exception:
            self._deinit()
            raise

    def reset(self):
        curses.endwin()

    def __del__(self):
        self.reset()
