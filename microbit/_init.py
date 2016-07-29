import logging
import os
import time

from microbit._simulator.display import MicroBitDisplay
from microbit._simulator.button import Button
from microbit._simulator.renderer import ANSIRenderer
from microbit._simulator.renderer import CursesRenderer
from microbit._simulator.simulator import Simulator

logging.basicConfig(level=logging.DEBUG, filename='/tmp/microbit.log')


def sleep(millis: int):
    """
    Sleep for ``millis``
    """
    time.sleep(millis / 1000)


simulator = Simulator()
running_time = simulator.running_time()

button_a = simulator.button_a
button_b = simulator.button_b


display = simulator.display

#
# _input_thread = threading.Thread(target=_input.watch_input,
#                                  args=[display._renderer.win, sys.stdin,
#                                        button_a,
#                                        button_b],
#                                  daemon=True)
# _input_thread.start()
#
#
