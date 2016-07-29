import time
from microbit._simulator.image import Image
from microbit._simulator.simulator import Simulator


__all__ = [
    'Image'
    'running_time',
    'sleep',
    'display',
    'button_a',
    'button_b',
]


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
