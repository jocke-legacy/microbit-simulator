import io
import logging
import sys
import threading
import time
from collections import deque

import zmq

from microbit._simulator import conf
from microbit._simulator.button import Button
from microbit._simulator.display import Display
from microbit._simulator.io import ZMQWritableStream
from microbit._simulator.logging import configure_logging

_log = logging.getLogger(__name__)


class patch_standard_io:
    def __init__(self, context: zmq.Context):
        self.real_stderr = sys.stderr
        self.real_stdout = sys.stdout
        self.stderr = ZMQWritableStream(conf.ZMQ_STDERR_SOCKET, context)
        self.stdout = ZMQWritableStream(conf.ZMQ_STDOUT_SOCKET, context)

    def start(self):
        sys.stdout = self.stdout
        #sys.stderr = self.stderr

    def stop(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        pass


class Simulator:
    def __init__(self):
        print('Hello')
        self.renderer = None
        self.display = Display(update_callback=self._on_display_update)
        self.button_a = Button('button_a')
        self.button_b = Button('button_b')
        self.time_start = time.time()

        self.zmq_context = zmq.Context()
        self.io_patch = patch_standard_io(self.zmq_context)
        _log.info('Simulator created')

    def start(self):
        _log.info('Starting %r', self)
        logging_data = LoggingData(self.zmq_context)
        logging_data.gather()
        self.renderer = conf.get_instance(conf.RENDERER,
                                          logging_data)
        configure_logging()
        _log.info('Hello!')
        self.io_patch.start()

    def stop(self):
        self.io_patch.stop()

    def _on_display_update(self):
        _log.debug('Update')
        self.renderer.render_display(self.display)

    def running_time(self) -> int:
        """
        Returns milliseconds since start.
        """
        now = time.time()
        _running_time = round((now - self.time_start) * 1000)
        return _running_time


class LoggingData:
    def __init__(self, context: zmq.Context, maxlen=1000):
        self.context = context
        self.messages = deque([], maxlen=maxlen)
        self.t_gather = None

    def gather(self):
        self.t_gather = threading.Thread(target=self.run_gather)
        self.t_gather.start()

    def run_gather(self):
        _log.info('Gathering')
        sub = self.context.socket(zmq.SUB)
        sub.setsockopt_string(zmq.SUBSCRIBE, '')
        sub.connect(conf.LOGGING_PUB_SOCKET)

        while True:
            self.messages.append(sub.recv_string())
