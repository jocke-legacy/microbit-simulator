import time

from datetime import datetime
import numpy as np
from microbit_sim.ui import common

import logging
import asyncio
import curses

from microbit_sim.inputevent import ButtonEvent
from microbit_sim.ui.curses_renderer import CursesRenderer
from microbit_sim.bus import AsyncBus
from microbit_sim.ui.common import end_curses_on_exception
from microbit_sim.ui.speedup import _speedup
#from microbit_sim.ui.speedup.zmq_interface import ZMQUIInterface
from microbit_sim.ui.speedup._speedup import  ratelimit

_log = logging.getLogger(__name__)


class AsyncIOCursesUI(CursesRenderer):
    def __init__(self, *, loop=None):
        self.bus = AsyncBus()
        self.tasks = []
        self.loop = loop or asyncio.get_event_loop()
        super().__init__()

    @end_curses_on_exception
    def run(self):
        self.start_curses()

        self.loop.call_soon(self.refresh_stats)

        self.add_task(self.listen_for_input())
        self.add_task(self.receive_control_messages())
        self.add_task(self.receive_display_updates())
        self.add_task(self.refresh_ui())
        self.loop.call_soon(self.print_tasks)

        self.loop.run_forever()

    async def monitor_task(self, coro):
        task = self.loop.create_task(coro)
        await task

    def add_task(self, coro):
        self.tasks.append(coro)
        task = self.loop.create_task(self.monitor_task(coro))

        def on_done(future):
            self.tasks.remove(coro)
            exc = future.exception()
            if exc:
                raise exc

        task.add_done_callback(on_done)

    def print_tasks(self):
        output = 'tasks:\n'
        for task in self.tasks:
            output += ' - {!r}\n'.format(task)

        self.add_output(output)
        self.loop.call_later(1, self.print_tasks)

    async def listen_for_input(self):
        ch = self.screen.getch()
        if ch != -1:
            _log.debug('ch=%r', ch)

        if ch == curses.KEY_LEFT:
            self.bus.send_input_event(ButtonEvent('button_a', 'press'))
        elif ch == curses.KEY_RIGHT:
            self.bus.send_input_event(ButtonEvent('button_b', 'press'))

        self.add_task(self.listen_for_input())

    def refresh_stats(self):
        self.render_stats()
        self.loop.call_later(1 / 60, self.refresh_stats)

    async def refresh_ui(self):
        t_last = 0
        min_delta = 1 / 60

        def sleep(delta, min_delta):
            yield from asyncio.sleep(min_delta - delta)

        # async for _ in ratelimit(1 / 60):
        while True:
            # Rate limiting
            t_now = time.time()
            delta_t = t_now - t_last

            if delta_t < min_delta:
                await asyncio.sleep(min_delta - delta_t)
            t_last = t_now

            self.update_timing('ui')

            self.screen.refresh()
            self.win_leds.refresh()
            self.win_output.refresh()

    async def receive_control_messages(self):
        control = await self.bus.recv_control()

        if control == 'stop':
            _log.warning('Stopping')
        else:
            _log.warning('Unknown control message: %r', control)

        self.add_task(self.receive_control_messages())

    async def receive_display_updates(self):
        while True:
            # _log.info('Display update')
            # message_type, display_data = await self.bus.recv_display()
            #
            # if message_type == b'display':
            #     self.render_display(display_data)
            # elif message_type == b'pixel':
            #     self.render_display_pixel(*display_data)
            buffer = await self.bus.recv_display()
            self.render_display(buffer)

            await asyncio.sleep(0)

        #self.add_task(self.receive_display_updates())

    @end_curses_on_exception
    def render_display_pixel(self, x, y, value):
        y, x = _speedup.led_y(y), _speedup.led_x(x)
        self.win_leds.addch(self.layout.leds.y + y,
                            self.layout.leds.x + x,
                            common.U_LOWER_HALF_BLOCK,
                            common.pair_for_value(value))
        self.win_leds.refresh()

    def led_y(self, y):
        return y + 1

    def led_x(self, x):
        return x * 2 + 2

    @end_curses_on_exception
    def render_display(self, buffer):
        #_log.debug('render_display(buffer=%r)', buffer)
        self.update_timing('render')

        self.win_leds.border()
        if False:
            _speedup.render_leds(self.win_leds,
                                 buffer,
                                 self.layout.microbit.y,
                                 self.layout.microbit.x)
        else:
            for (y, x), value in np.ndenumerate(buffer):
                self.win_leds.addch(self.led_y(y),
                          self.led_x(x),
                          common.U_LOWER_HALF_BLOCK,
                          common.pair_for_value(value))

            #self.win_leds.refresh()

    def render_stats(self):
        # self.win_stats.clear()
        self.update_timing('stats')
        self.win_stats.addstr(0, 0,
                              '{datetime}: '
                              'render: {counters[render]:.2f}/s, '
                              'mainloop: {counters[mainloop]:.2f}/s, '
                              'stats: {counters[stats]:.2f}/s, '
                              'ui: {counters[ui]:.2f}/s'
                              .format(counters=self.counters,
                                      datetime=datetime.now().isoformat(sep=' ')))
        self.win_stats.noutrefresh()
