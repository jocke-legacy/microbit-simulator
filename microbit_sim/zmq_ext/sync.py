import zmq
from . import base


class Socket(base.Socket):
    def _func_wrapper(self, func, *args, **kwargs):
        return func(*args, **kwargs)


class Context(zmq.Context):
    @property
    def _socket_class(self):
        return Socket
