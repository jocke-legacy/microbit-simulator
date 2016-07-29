import logging

import zmq

_log = logging.getLogger(__name__)


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
