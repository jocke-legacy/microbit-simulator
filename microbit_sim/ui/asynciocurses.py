import time
from collections import defaultdict
from collections import deque

from datetime import datetime

import numpy as np
from microbit_sim.ui import common

import logging
import asyncio
import curses

from microbit_sim.inputevent import ButtonEvent
from microbit_sim.bus import AsyncBus
from microbit_sim.ui.common import end_curses_on_exception
from microbit_sim.ui.display_interface import ZMQDisplayInterface
from microbit_sim.ui.speedup import common as _common

_log = logging.getLogger(__name__)

COUNTER_SMOOTHING = 0.9


class AsyncIOCursesUI:
    def __init__(self, *, loop=None):
        self.bus = AsyncBus()
        self.tasks = []
        self.loop = loop or asyncio.get_event_loop()

        self.output_lines = deque([''], maxlen=common.OUTPUT_MAX_LINES)

        self.layout = None

        # Curses
        self.screen = None
        self.win = None

        # Stats
        self._counters_last = {}

        self.counters = defaultdict(lambda: 0)

    def update_timing(self, name):
        t_now, average = common.update_timing_average(
            self._counters_last.setdefault(name, 0.0),
            self.counters.setdefault(name, 0.0))

        self._counters_last[name] = t_now
        self.counters[name] = average

    @end_curses_on_exception
    def start_curses(self):
        self.screen = common.start_curses()

        # Layout
        self.layout = common.update_layout(self.screen)

        # Windows
        self.win = common.create_windows(self.screen, self.layout)

    def create_task(self, coro):
        self.tasks.append(coro)
        task = self.loop.create_task(coro)

        def on_done(future):
            self.tasks.remove(coro)
            exc = future.exception()
            if exc:
                raise exc

        task.add_done_callback(on_done)

    @end_curses_on_exception
    def run(self):
        self.start_curses()

        self.loop.call_soon(self.refresh_stats)

        ZMQDisplayInterface(self.render_display_pixel)

        # self.create_task(self.listen_for_input())
        # self.add_task(self.receive_control_messages())
        # self.create_task(self.receive_display_updates())
        self.create_task(self.refresh_ui())
        self.loop.call_soon(self.print_tasks)
        self.loop.run_forever()

    def print_tasks(self):
        output = 'tasks:\n'
        for task in self.tasks:
            output += ' - {!r}\n'.format(task)

        self.add_output(output)
        self.loop.call_later(10, self.print_tasks)

    async def listen_for_input(self):
        ch = self.screen.getch()
        if ch != -1:
            _log.debug('ch=%r', ch)

        if ch == curses.KEY_LEFT:
            self.bus.send_input_event(ButtonEvent('button_a', 'press'))
        elif ch == curses.KEY_RIGHT:
            self.bus.send_input_event(ButtonEvent('button_b', 'press'))

        self.create_task(self.listen_for_input())

    def refresh_stats(self):
        self.render_stats()
        self.loop.call_later(1 / 60, self.refresh_stats)

    async def refresh_ui(self):
        _log.info('Refreshing UI')
        t_last = 0
        min_delta = 1 / 60

        async for _ in common.ratelimit(1 / 60):
        # while True:
        #     await asyncio.sleep(0)
            self.update_timing('ui')

            self.screen.refresh()
            self.win.leds.refresh()
            self.win.output.refresh()

    async def receive_control_messages(self):
        control = await self.bus.recv_control()

        if control == 'stop':
            _log.warning('Stopping')
        else:
            _log.warning('Unknown control message: %r', control)

        self.create_task(self.receive_control_messages())

    #@common.tail_recursive
    async def receive_display_updates(self):
        async for _ in common.ratelimit(1 / 10000):
            buffer = await self.bus.recv_display()
            self.render_display(buffer)
        # try:
        #     fut = asyncio.ensure_future(self.bus.recv_display())
        #     buffer = await asyncio.wait_for(fut, 0)
        #     self.update_timing('recv_display')
        # except:
        #     self.update_timing('recv_timeout')
        # else:
        #     self.render_display(fut.result())
        # self.create_task(self.receive_display_updates())

        #self.add_task(self.receive_display_updates())

    @end_curses_on_exception
    def render_display_pixel(self, x, y, value):
        self.update_timing('render')
        y, x = self.led_y(y), self.led_x(x)
        self.win.leds.addch(y,
                            x,
                            common.U_LOWER_HALF_BLOCK,
                            common.pair_for_value(value))

    def led_y(self, y):
        return y + 1

    def led_x(self, x):
        return x * 2 + 2

    @end_curses_on_exception
    def render_display(self, buffer):
        #self.update_timing('render')

        if False:
            _common.render_leds(self.win.leds,
                                 buffer,
                                 self.layout.microbit.y,
                                 self.layout.microbit.x)
        else:
            for (y, x), value in np.ndenumerate(buffer):
                self.win.leds.addch(self.led_y(y),
                                    self.led_x(x),
                                    common.U_LOWER_HALF_BLOCK,
                                    common.pair_for_value(value))

        #self.win.leds.refresh()

    def render_stats(self):
        # self.win.stats.clear()
        self.update_timing('stats')
        self.win.stats.addstr(
            0, 0,
            '{datetime}: '
            'render: {counters[render]:.2f}/s, '
            'recv_display: {counters[recv_display]:.2f}/s, '
            'stats: {counters[stats]:.2f}/s, '
            'ui: {counters[ui]:.2f}/s'
            .format(counters=self.counters,
                    datetime=datetime.now().isoformat(sep=' ')))
        self.win.stats.refresh()

    def add_output(self, output):
        _log.debug('add_output(output=%r)', output)
        lines = output.split('\n')
        first, *rest = lines
        self.output_lines[-1] += first
        self.output_lines.extend(rest)
        self.render_output()

    def render_output(self):
        self.update_timing('output')

        self.win.output_pad.clear()
        for i, line in enumerate(self.output_lines):
            self.win.output_pad.addstr(i + 1, 0, line)

        pad_min_y = max(
            len(self.output_lines) - self.layout.output.height, 0)
        self.win.output_pad.noutrefresh(
            pad_min_y,
            0,
            self.layout.output.y + 1,
            self.layout.output.x + 1,
            self.layout.output.y2 - 2,
            self.layout.output.x2 - 1)
