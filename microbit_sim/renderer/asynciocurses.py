import logging
import zmq.asyncio
import asyncio
import curses

from microbit_sim.inputevent import ButtonEvent
from microbit_sim.logging import configure_logging
from microbit_sim.renderer import CursesRenderer
from microbit_sim.communication import AsyncBus

_log = logging.getLogger(__name__)


class AsyncIOCursesRenderer(CursesRenderer):
    def __init__(self):
        super().__init__()

        self.bus = AsyncBus()
        self.tasks = []

    def run(self, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        self.loop = loop

        self.start_curses()

        self.add_task(self.refresh_stats())
        self.add_task(self.listen_for_input())
        self.add_task(self.receive_control_messages())
        self.add_task(self.receive_display_updates())
        self.print_tasks()

        loop.run_forever()

        self.end_curses()

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
        self.loop.call_later(5, self.print_tasks)

    async def listen_for_input(self):
        ch = self.win_leds.getch()
        if ch != -1:
            _log.debug('ch=%r', ch)

        if ch == curses.KEY_LEFT:
            self.bus.send_input_event(ButtonEvent('button_a', 'press'))
        elif ch == curses.KEY_RIGHT:
            self.bus.send_input_event(ButtonEvent('button_b', 'press'))

        self.add_task(self.listen_for_input())

    async def refresh_stats(self):
        self.update_timing('stats')
        self.render_stats()

        self.loop.call_later(1 / 60,
                             lambda: self.add_task(self.refresh_stats()))

    async def receive_control_messages(self):
        control = await self.bus.recv_control()

        if control == 'stop':
            _log.warning('Stopping')
        else:
            _log.warning('Unknown control message: %r', control)

        self.add_task(self.receive_control_messages())

    async def receive_display_updates(self):
        #_log.debug('Waiting for display update')
        buffer = await self.bus.recv_display()
        self.render_display(buffer)
        self.add_task(self.receive_display_updates())


if __name__ == '__main__':
    # loop = zmq.asyncio.ZMQEventLoop()
    # asyncio.set_event_loop(loop)
    configure_logging(filename='/tmp/microbit-renderer.log')
    try:
        AsyncIOCursesRenderer().run()
    finally:
        if not curses.isendwin():
            curses.endwin()
