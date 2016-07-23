from collections import namedtuple
import curses

from . import display


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


def main(stdscr):
    curses.start_color()
    stdscr.clear()


curses.wrapper(main)
