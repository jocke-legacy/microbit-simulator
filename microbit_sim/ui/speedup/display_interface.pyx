import logging
import asyncio
import zmq.asyncio
#cimport zmq.backend.cython.socket as _socket
#cimport zmq.backend.cython.context as _context

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
        self._init()
        self.loop.create_task(self.listen_pixels())

    def _init(self):
        ctx = zmq.asyncio.Context()
        pixel_socket = ctx.socket(zmq.PULL)

        pixel_socket.connect(conf.DISPLAY_SOCKET)
        self.pixel_socket = pixel_socket
        self.ctx = ctx

    async def listen_pixels(self):
        while True:
            args = await self.pixel_socket.recv_multipart()
            self.on_render_pixel(*args)
