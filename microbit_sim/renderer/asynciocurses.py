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

    def run(self, *, loop=None):
        loop = loop or asyncio.get_event_loop()

        self.start_curses()

        display_task = loop.create_task(self.receive_display_updates())
        loop.create_task(self.refresh_stats())
        loop.create_task(self.listen_for_input())
        loop.create_task(self.receive_control_messages())
        loop.run_until_complete(display_task)

        self.end_curses()

    async def listen_for_input(self):
        while True:
            ch = self.win_leds.getch()

            if ch == curses.KEY_LEFT:
                self.bus.send_input_event(ButtonEvent('button_a', 'press'))
            elif ch == curses.KEY_RIGHT:
                self.bus.send_input_event(ButtonEvent('button_b', 'press'))
            await asyncio.sleep(1)

    async def refresh_stats(self):
        while True:
            self.render_stats()
            await asyncio.sleep(1 / 60)

    async def receive_control_messages(self):
        while True:
            _log.info('Waiting for control message')
            control = await self.bus.recv_control()
            if control == 'stop':
                _log.warning('Stopping')

    async def receive_display_updates(self):
        while True:
            _log.debug('Waiting for display update')
            buffer = await self.bus.recv_display()
            _log.debug('buffer=%r', buffer)
            self.render_display(buffer)


if __name__ == '__main__':
    loop = zmq.asyncio.ZMQEventLoop()
    asyncio.set_event_loop(loop)
    configure_logging(filename='/tmp/microbit-renderer.log')
    try:
        AsyncIOCursesRenderer().run()
    finally:
        if not curses.isendwin():
            curses.endwin()
