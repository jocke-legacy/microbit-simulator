from typing import Union

import numpy as np

from . import base


class Image(base.ImageData):
    def __init__(self, text_or_width: Union[str, int]=5, height=5, buf=None):
        string = None
        if isinstance(text_or_width, int):
            width = text_or_width
        else:
            string = text_or_width
            width = 5

        # Initialize ImageData once we've figured out our width and height
        super(Image, self).__init__(width=width, height=height)

        if string is not None:
            # Parse string representation of an image
            self._set_from_string(string)

        if buf is not None:
            # Broadcast ``buf`` into our underlying buffer
            self._buffer[:] = buf

    def width(self):
        return self._buffer.shape[1]

    def height(self):
        return self._buffer.shape[0]

    def __repr__(self):
        return 'Image({!r})'.format(self._repr_str())

    def shift_left(self, n):
        return self._shift(2, n)

    def shift_right(self, n):
        return self._shift(3, n)

    def shift_up(self, n):
        return self._shift(0, n)

    def shift_down(self, n):
        return self._shift(1, n)

    def _shift(self, direction: int, amount: int):
        """
        Shift image pixels towards a certain direction.

        :param direction: 0, 1, 2, 3 = top, bottom, left, right
        :param amount:
        :return:
        """
        (top, bottom,
         left, right) = [amount if i == direction else None
                         for i in range(0, 4)]

        slice_y = slice(top or None,
                        -bottom if bottom is not None else None)
        slice_x = slice(left,
                        -right if right is not None else None)

        pad = np.array([i if i is not None
                        else 0
                        for i in (bottom, top,
                                  right, left)],
                       dtype=int).reshape(2, 2)
        self._buffer = np.pad(self._buffer,
                              # Only accepts tuples
                              tuple(tuple(i) for i in pad),
                              mode='constant')[slice_y, slice_x]

    def crop(self, x, y, w, h):
        self._buffer = self._buffer[y:y + h, x:x + w]

    def invert(self):
        self._buffer = 9 - self._buffer  # type: np.ndarray

    def __str__(self):
        return (
            'Image(\n' +
            sum(['    {}\n'.format(line) for line in self._repr_rows], '') +
            ')\n'
        )

    def __add__(self, other):
        raise NotImplementedError

    def __mul__(self, other):
        raise NotImplementedError
