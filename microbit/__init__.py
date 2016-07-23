from ._microbitdisplay import MicroBitDisplay
import time

_TIME_INIT = time.time()


def running_time() -> int:
    """
    Returns milliseconds since start.
    """
    now = time.time()
    _running_time = round((now - _TIME_INIT) * 1000)
    return _running_time


def sleep(millis: int):
    """Sleep for ``millis``"""
    time.sleep(millis / 1000)


class Image:
    def __init__(self, *args, **kwargs):
        pass

    def width(self):
        return self._width

    def height(self):
        return self._height

    def set_pixel(self, x, y, value):
        pass

    def get_pixel(self, x, y):
        pass

    def shift_left(self, n):
        pass

    def shift_right(self, n):
        pass

    def shift_up(self, n):
        pass

    def shift_down(self, n):
        pass

    def crop(self, x, y, w, h):
        pass

    def copy(self):
        pass

    def invert(self):
        pass

    def __str__(self):
        pass

    def __repr__(self):
        pass

    def __add__(self, other):
        pass

    def __mul__(self, other):
        pass


display = MicroBitDisplay()
