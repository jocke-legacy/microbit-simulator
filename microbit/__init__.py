from microbit_sim.simulator import Simulator
from microbit_sim.stub.image import Image

__all__ = [
    'Image'
    'running_time',
    'sleep',
    'display',
    'button_a',
    'button_b',
]


_simulator = Simulator()
running_time = _simulator.running_time
sleep = _simulator.sleep

button_a = _simulator.button_a
button_b = _simulator.button_b

display = _simulator.display

_simulator.start()
