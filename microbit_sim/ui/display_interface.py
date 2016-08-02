import logging
import asyncio

import zmq.asyncio

from microbit_sim import conf

_log = logging.getLogger(__name__)


class ZMQDisplayInterface:
    """
    Connects to the display socket.

    Display data:
    - Simulator: zmq.PUSH
    - Display: zmq.PULL

    """
    def __init__(self, on_render_pixel, *, loop=None):
        _log.info('Starting %r', self)
        self.loop = loop or asyncio.get_event_loop()
        self.on_render_pixel = on_render_pixel

        self.ctx = zmq.asyncio.Context()
        self.pixel_socket = self.ctx.socket(zmq.PULL)
        self.pixel_socket.hwm = 1

        self.pixel_socket.connect(conf.DISPLAY_PIXEL_SOCKET)

        def on_done(fut):
            exc = fut.exception()
            if exc:
                raise exc

        self.loop.create_task(self.listen_pixels()).add_done_callback(on_done)

    async def listen_pixels(self):
        while True:
            data = await self.pixel_socket.recv()
            x, y, value = bytearray(data)
            self.on_render_pixel(x, y, value)
