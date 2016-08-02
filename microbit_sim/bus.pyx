import logging
import functools
from abc import ABCMeta, abstractproperty, abstractmethod

import umsgpack
import numpy
import zmq
from microbit_sim import inputevent

from . import conf, zmq_ext

_log = logging.getLogger(__name__)


class AbstractBus(metaclass=ABCMeta):
    @abstractproperty
    def context(self):
        pass


class BaseSocketDeclaration:
    def __init__(self, socket: zmq_ext.base.Socket, addr: str,
                 established=False):
        self.established = established
        self.addr = addr
        self.socket = socket

    @abstractmethod
    def ensure_established(self) -> zmq_ext.base.Socket:
        pass


class Connect(BaseSocketDeclaration):
    def ensure_established(self) -> zmq_ext.base.Socket:
        if not self.established:
            self.socket.connect(self.addr)
            self.established = True

        return self.socket


class Bind(BaseSocketDeclaration):
    def ensure_established(self) -> zmq_ext.base.Socket:
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

        control_socket = self.context.socket(zmq_ext.PAIR)
        input_send_socket = self.context.socket(zmq_ext.PUSH)
        input_recv_socket = self.context.socket(zmq_ext.PULL)

        display_send_socket = self.context.socket(zmq_ext.PUSH)
        display_send_socket.hwm = 1
        display_recv_socket = self.context.socket(zmq_ext.PULL)
        display_recv_socket.hwm = 1

        self.sockets = {
            'display': {
                'recv': Connect(display_recv_socket,
                                conf.DISPLAY_SOCKET),
                'send': Bind(display_send_socket,
                             conf.DISPLAY_SOCKET),
            },
            'display-pixel': {
                'recv': Connect(self.context.socket(zmq.PULL),
                                conf.DISPLAY_PIXEL_SOCKET),
                'send': Bind(self.context.socket(zmq.PUSH),
                             conf.DISPLAY_PIXEL_SOCKET)
            },
            'control': {
                'recv': Bind(control_socket, conf.CONTROL_SOCKET),
                'send': Connect(control_socket, conf.CONTROL_SOCKET),
            },
            'input-events': {
                'recv': Bind(input_recv_socket,
                             conf.INPUT_EVENTS_SOCKET),
                'send': Connect(input_send_socket,
                                conf.INPUT_EVENTS_SOCKET)
            }
        }

        self._bound = set()
        self._connected = set()

    def get_socket(self, socket_name, socket_type) -> zmq_ext.base.Socket:
        return self.sockets[socket_name][socket_type].ensure_established()

    def _send_socket(self, socket_name) -> zmq_ext.base.Socket:
        return self.get_socket(socket_name, socket_type='send')

    def _recv_socket(self, socket_name) -> zmq_ext.base.Socket:
        return self.get_socket(socket_name, socket_type='recv')

    def get_socket_addr(self, socket_name):
        return self.sockets[socket_name]['addr']

    def __repr__(self):
        return '<{self.__class__.__name__} {self.stats!r}>'.format(self=self)

    def __del__(self):
        print('deleting: %r' % self)


class Bus(BaseBus):
    """

    """
    @property
    def context(self):
        if self._context is None:
            self._context = zmq_ext.sync.Context()

        return self._context

    @incr_stats_sent
    def send_display(self, buffer):
        return self._send_socket('display').send_array(buffer)

    @incr_stats_sent
    def send_display_pixel(self, x, y, value):
        return self._send_socket('display-pixel').send(
            bytearray([x, y, value]))

    @incr_stats_sent
    def send_control(self, control):
        return self._send_socket('control').send_msgpack(control)

    @incr_stats_rcvd
    def recv_input_event(self):
        return inputevent.unpack(
            self._recv_socket('input-events').recv_msgpack())


class AsyncBus(BaseBus):
    @property
    def context(self):
        if self._context is None:
            self._context = zmq_ext.asyncio.Context()
        return self._context

    @incr_stats_rcvd
    async def recv_display(self):
        return self._recv_socket('display').recv_array()
        # message_type, *message_rest = self._recv_socket('display')\
        #     .recv_multipart()
        #
        # if message_type == b'display':
        #     return message_type, unpack_array(*message_rest)
        # elif message_type == b'pixel':
        #     return message_type, message_rest
        # else:
        #     raise ValueError('Unknown message type {!r}'.format(message_type))

    @incr_stats_rcvd
    def recv_control(self):
        return self._recv_socket('control').recv_msgpack()

    @incr_stats_sent
    def send_input_event(self, event):
        return self._send_socket('input-events').send_msgpack(
            inputevent.pack(event))


def send_array(socket, numpy_array, flags=0, copy=True, track=False):
    """
    Send a numpy array with metadata.
    """
    return socket.send_multipart(pack_array(numpy_array),
                                 flags=flags,
                                 copy=copy,
                                 track=track)


async def recv_array(socket, flags=0, copy=True, track=False):
    multipart = await socket.recv_multipart(flags=flags, copy=copy,
                                            track=track)
    metadata_bytes, msg = multipart
    return unpack_array(metadata_bytes, msg)


def pack_array(numpy_array):
    metadata = dict(
        dtype=str(numpy_array.dtype),
        shape=numpy_array.shape,
    )
    return [umsgpack.packb(metadata), numpy_array]


def unpack_array(metadata_bytes, buffer):
    metadata = umsgpack.unpackb(metadata_bytes)
    buf = memoryview(buffer)
    numpy_array = numpy.frombuffer(buf, dtype=metadata['dtype'])
    return numpy_array.reshape(metadata['shape'])
