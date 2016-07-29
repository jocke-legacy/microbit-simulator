import copy
from typing import List

import numpy as np

from microbit._simulator import abstract


class ImageData(abstract.ImageData):
    _STR_SEP = ':\n'

    def __init__(self, width=5, height=5):
        self._buffer = None
        self._new_buffer(width=width, height=height)

    @property
    def _width(self):
        return self._buffer.shape[1]

    @property
    def _height(self):
        return self._buffer.shape[0]

    def _new_buffer(self, width, height):
        self._buffer = np.zeros((height, width), dtype=np.uint8)

    def _repr_rows(self) -> List[str]:
        rows = []
        for line in self._buffer:
            line_string = ''.join(str(value) for value in line)
            rows.append('{}:'.format(line_string))

        return rows

    def _repr_str(self) -> str:
        """
        Get the string representation of the image as one string
        """
        return sum(self._repr_rows(), '')

    def _set_from_string(self, string: str):
        if not string:
            self._buffer = np.zeros_like(self._buffer)

        rows = string.rstrip(self._STR_SEP).split(self._STR_SEP)

        width = max([len(r) for r in rows])
        height = len(rows)
        self._new_buffer(width=width, height=height)

        return [[int(char) for char in r.ljust(width, '0')]
                for r in rows]

    def get_pixel(self, x, y):
        return self._buffer[y, x]

    def set_pixel(self, x, y, value):
        assert 0 <= value < 10
        self._buffer[y, x] = value

    def __str__(self):
        return sum(('{}:'.format([str(value) for value in line])
                    for line in self._buffer), start='')

    def copy(self):
        return copy.copy(self)
