import pyximport; pyximport.install()

import logging
import curses
import queue
from collections import defaultdict
from collections import deque
from datetime import datetime

import time

from microbit_sim.renderer.speedup import _speedup

from microbit_sim.renderer.abstract import AbstractRenderer
from microbit_sim.renderer.common import start_curses, end_curses_on_exception, update_layout

COUNTER_SMOOTHING = 0.9

_log = logging.getLogger(__name__)


class CursesRenderer(AbstractRenderer):
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

    @end_curses_on_exception
    def start_curses(self):
        self.screen = start_curses()

        # Layout
        self.layout = update_layout(self.screen)

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

    @end_curses_on_exception
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

    def render_stats(self):
        self.win_stats.clear()
        self.win_stats.addstr(
            '{datetime}: '
            'render: {counters[render]:.2f}/s, '
            'mainloop: {counters[mainloop]:.2f}/s, '
            'stats: {counters[stats]:.2f}/s'
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

    @end_curses_on_exception
    def get_input(self):
        from microbit import button_a, button_b

        ch = self.win_leds.getch()

        if ch == curses.KEY_LEFT:
            button_a._press()
        elif ch == curses.KEY_RIGHT:
            button_b._press()

    @end_curses_on_exception
    def render_display(self, buffer):
        #_log.debug('render_display(buffer=%r)', buffer)
        self.update_timing('render')
        #
        # def led_x(x):
        #     return self.layout.microbit.x + x * 2 + 2
        #
        # def led_y(y):
        #     return self.layout.microbit.y + y + 1

        self.win_leds.border()
        args = _speedup.render_leds(buffer, self.layout.microbit.y,
                                    self.layout.microbit.x)
        for y, x, char, pair_number in args:

            self.win_leds.addch(y, x,
                                char,
                                curses.color_pair(pair_number))

        self.win_leds.refresh()
