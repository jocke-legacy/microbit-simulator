import logging

import sys
import zmq
from . import conf

_log = logging.getLogger(__name__)


class patch_standard_io:
    def __init__(self, stdout, stderr):
        self.real_stderr = sys.stderr
        self.real_stdout = sys.stdout
        self.stderr = stderr
        self.stdout = stdout

    def start(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def stop(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        pass


class QueueWritableStream:
    def __init__(self, queue: 'Queue'):
        self.queue = queue

    def write(self, data):
        self.queue.put_nowait(data)


class ZMQWritableStream:
    def __init__(self, socket_addr, context: zmq.Context):
        self.socket_addr = socket_addr
        self.socket = context.socket(zmq.PUSH)
        self.socket.bind(socket_addr)

    def __repr__(self):
        return '<{name} {socket!r}>'.format(name=self.__class__.__name__,
                                            socket=self.socket)

    def write(self, str):
        return self.socket.send_string(str)

    def flush(self):
        pass


