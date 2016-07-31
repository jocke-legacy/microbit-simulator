import io
import json
import logging
import functools
from abc import ABCMeta, abstractproperty, abstractmethod

import numpy
import zmq
import zmq.asyncio

from . import conf

_log = logging.getLogger(__name__)


class AbstractBus(metaclass=ABCMeta):
    @abstractproperty
    def context(self):
        pass


class BaseSocketDeclaration:
    def __init__(self, socket: zmq.Socket, addr: str, established=False):
        self.established = established
        self.addr = addr
        self.socket = socket

    @abstractmethod
    def ensure_established(self) -> zmq.Socket:
        pass


class Connect(BaseSocketDeclaration):
    def ensure_established(self) -> zmq.Socket:
        if not self.established:
            self.socket.connect(self.addr)
            self.established = True

        return self.socket


class Bind(BaseSocketDeclaration):
    def ensure_established(self) -> zmq.Socket:
        if not self.established:
            self.socket.bind(self.addr)
            self.established = True

        return self.socket


def make_stats_incr(key):
    def incr_wrapper(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            self.stats[key] += 1
            return result

        return wrapper

    return incr_wrapper

incr_stats_sent = make_stats_incr('sent')
incr_stats_rcvd = make_stats_incr('rcvd')


class BaseBus(AbstractBus):
    def __init__(self):
        self.stats = {
            'sent': 0,
            'rcvd': 0,
        }

        self._context = None

        control_socket = self.context.socket(zmq.PAIR)

        self.sockets = {
            'display': {
                'recv': Connect(self.context.socket(zmq.PULL),
                                conf.DISPLAY_SOCKET),
                'send': Bind(self.context.socket(zmq.PUSH),
                             conf.DISPLAY_SOCKET),
            },
            'control': {
                'recv': Bind(control_socket, conf.CONTROL_SOCKET),
                'send': Connect(control_socket, conf.CONTROL_SOCKET),
            }
        }

        self._bound = set()
        self._connected = set()

    def get_socket(self, socket_name, socket_type) -> zmq.Socket:
        return self.sockets[socket_name][socket_type].ensure_established()

    def send_socket(self, socket_name) -> zmq.Socket:
        return self.get_socket(socket_name, socket_type='send')

    def recv_socket(self, socket_name) -> zmq.Socket:
        return self.get_socket(socket_name, socket_type='recv')

    def get_socket_addr(self, socket_name):
        return self.sockets[socket_name]['addr']

    def __repr__(self):
        return '<{self.__class__.__name__} {self.stats!r}>'.format(self=self)

    def __del__(self):
        print('deleting: %r' % self)


class Bus(BaseBus):
    @property
    def context(self):
        if self._context is None:
            self._context = zmq.Context()

        return self._context

    @incr_stats_sent
    def send_display(self, buffer):
        return send_array(self.send_socket('display'), buffer)

    @incr_stats_sent
    def send_control(self, control):
        return self.send_socket('display').send_string(control)


class AsyncBus(BaseBus):
    @property
    def context(self):
        if self._context is None:
            self._context = zmq.asyncio.Context()
        return self._context

    @incr_stats_rcvd
    async def recv_display(self):
        return await recv_array(self.recv_socket('display'))

    @incr_stats_rcvd
    async def recv_control(self):
        return (await self.recv_socket('control').recv()).decode('utf-8')


def send_array(socket, A, flags=0, copy=True, track=False):
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
    )
    socket.send_json(md, flags | zmq.SNDMORE)
    return socket.send(A, flags, copy=copy, track=track)


async def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = await recv_json(socket, flags=flags)
    msg = await socket.recv(flags=flags, copy=copy, track=track)
    buf = memoryview(msg)
    A = numpy.frombuffer(buf, dtype=md['dtype'])
    return A.reshape(md['shape'])


async def recv_json(socket, flags=0, **kwargs):
    return json.loads((await socket.recv(flags=flags)).decode('utf-8'),
                      **kwargs)


