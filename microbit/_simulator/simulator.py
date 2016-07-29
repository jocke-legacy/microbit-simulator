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
from microbit._simulator.logging import configure_logging

_log = logging.getLogger(__name__)


class Simulator:
    def __init__(self):
        self.renderer = None

        self.display = Display(update_callback=self._on_display_update)

        self.button_a = Button('button_a')
        self.button_b = Button('button_b')
        self.time_start = time.time()

        self.zmq_context = zmq.Context()

    def start(self):
        _log.info('Starting %r', self)
        # logging_data = LoggingData(self.zmq_context)
        # logging_data.gather()
        self.renderer = conf.get_instance(conf.RENDERER)
        configure_logging()

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
