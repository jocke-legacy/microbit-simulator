import logging
import zmq.asyncio
import asyncio
import curses

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

        loop.create_task(self.receive_display_updates())
        loop.create_task(self.refresh_stats())
        loop.run_until_complete(self.receive_control_messages())

        self.end_curses()

    async def listen_for_input(self):
        while True:
            self.get_input()
            await asyncio.sleep(1)

    async def refresh_stats(self):
        while True:
            self.render_stats()
            await asyncio.sleep(1)

    async def receive_control_messages(self):
        while True:
            _log.info('Waiting for control message')
            control = await self.bus.recv_control()
            if control == 'stop':
                break

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
