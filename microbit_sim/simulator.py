import atexit
import logging
import threading
import time
from collections import deque

import zmq
from microbit_sim.stub.button import Button
from microbit_sim.stub.display import Display

from . import conf
from .communication import Bus
from .io import patch_standard_io, ZMQWritableStream
from .logging import configure_logging

_log = logging.getLogger(__name__)


class Simulator:
    """
    Implements, or provides implementations for all ``microbit`` API methods
    and objects that need simulation.

    Communicates via a ``Bus`` instance with a ``Renderer`` instance created by
    another process.
    """
    def __init__(self):
        self.display = Display(update_callback=self.on_display_update)

        self.button_a = Button('button_a')
        self.button_b = Button('button_b')

        self.time_start = time.time()

        self.zmq_context = zmq.Context()

        self.bus = Bus()

        configure_logging(filename='/tmp/microbit-simulator.log')

        out_stream = ZMQWritableStream(conf.ZMQ_STDOUT_SOCKET,
                                       self.zmq_context)

        self.io_patch = patch_standard_io(stdout=out_stream,
                                          stderr=out_stream)

        self.renderer = None
        self.gui_thread = None
        self._time_last_display_update = 0

    def start(self):
        _log.info('Starting %r', self)

        atexit.register(self.stop)

    def on_display_update(self, buffer):
        # # Rate limiting
        # t_now = time.time()
        # delta_t = t_now - self._time_last_display_update
        #
        # if delta_t < 1 / 60:
        #     return
        #
        # self._time_last_display_update = t_now

        self.bus.send_display(buffer)
        #self.queues.display.put(buffer)
        #self.renderer.render_display(buffer)

    def stop(self):
        self.bus.send_control('stop')
        # self.queues.control.put_nowait('stop')
        del self.renderer

        # self.io_patch.stop()
        _log.info('Stopping')
        # output = self.queues.output  # type: queue.Queue
        # if not output.empty():
        #     while True:
        #         try:
        #             item = output.get_nowait()
        #         except queue.Empty:
        #             break
        #         else:
        #             self.io_patch.real_stdout.write(item)

    def sleep(self, millis: int):
        """
        Sleep for ``millis``
        """
        time.sleep(millis / 1000)

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
