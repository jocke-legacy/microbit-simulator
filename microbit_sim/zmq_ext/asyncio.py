import zmq.asyncio
from . import base


class Socket(base.Socket):
    def _func_wrapper(self, func, *args, **kwargs):
        return (yield from func(*args, **kwargs))


class Context(zmq.asyncio.Context):
    @property
    def _socket_class(self):
        return Socket
