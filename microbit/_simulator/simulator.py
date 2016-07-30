import logging
import queue
import threading
import time
from collections import deque

import atexit
import zmq
from microbit._simulator.base import Queues
from microbit._simulator.io import patch_standard_io, QueueWritableStream

from . import conf
from .button import Button
from .display import Display
from .logging import configure_logging

_log = logging.getLogger(__name__)


class Simulator:
    def __init__(self):
        self.display = Display(update_callback=self.on_display_update)

        self.button_a = Button('button_a')
        self.button_b = Button('button_b')

        self.time_start = time.time()

        self.zmq_context = zmq.Context()

        self.queues = Queues(
            control=queue.Queue(),
            display=queue.Queue(),
            output=queue.Queue(),
            logging=queue.Queue(),
        )

        out_stream = QueueWritableStream(self.queues.output)

        self.io_patch = patch_standard_io(stdout=out_stream,
                                          stderr=out_stream)

        self.renderer = None
        self.gui_thread = None

    def start(self):
        _log.info('Starting %r', self)

        configure_logging(self.queues.logging)
        # logging_data = LoggingData(self.zmq_context)
        # logging_data.gather()
        self.renderer = conf.get_instance(conf.RENDERER,
                                          queues=self.queues)
        self.io_patch.start()
        self.gui_thread = threading.Thread(target=self.renderer.run)
        self.gui_thread.start()

        atexit.register(self.stop)

    def on_display_update(self, buffer):
        _log.debug('Update')
        self.queues.display.put_nowait(buffer)
        #self.renderer.render_display(buffer)

    def stop(self):
        self.queues.control.put_nowait('stop')
        del self.renderer

        self.io_patch.stop()
        output = self.queues.output  # type: queue.Queue
        if not output.empty():
            while True:
                try:
                    item = output.get_nowait()
                except queue.Empty:
                    break
                else:
                    self.io_patch.real_stdout.write(item)

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
