import io
import logging

import time

import sys

from microbit._simulator import renderer
from microbit._simulator.button import Button
from microbit._simulator.display import MicroBitDisplay
from microbit._simulator import conf

_log = logging.getLogger(__name__)


class patch_standard_io:
    def __init__(self):
        self.real_stderr = sys.stderr
        self.real_stdout = sys.stdout
        self.stderr = io.StringIO()
        self.stdout = io.StringIO()

    def start(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr

    def stop(self):
        sys.stdout = self.real_stdout
        sys.stderr = self.real_stderr

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class Simulator:
    def __init__(self):
        self.display = MicroBitDisplay()
        self.button_a = Button('button_a')
        self.button_b = Button('button_b')

        self.renderer = conf.RENDERER
        self.time_start = time.time()

        self.io_patch = patch_standard_io()

        logging.basicConfig(level=)

    def start(self):
        self.io_patch.start()

    def stop(self):
        self.io_patch.stop()

    def _on_display_update(self):
        self.renderer.render(self.display)

    def running_time(self) -> int:
        """
        Returns milliseconds since start.
        """
        now = time.time()
        _running_time = round((now - self.time_start) * 1000)
        return _running_time

