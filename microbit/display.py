from typing import Iterable

import curses

from . import Image

_display_on = True


def on():
    global _display_on
    _display_on = True

def off():
    global _display_on
    _display_on = False


def is_on():
    return _display_on


def get_pixel(x, y):
    pass


def set_pixel(x, y, value):
    pass


def clear():
    curses.clear()


def scroll(string, delay=150, wait=True, loop=False, monospace=False):
    pass


def show(*args, **kwargs):
    def show_image(image):
        pass


    def show_iterable(iterable, delay=400, wait=True, loop=False,
                      clear=False):
        pass

    first_arg = args[0]
    if isinstance(first_arg, Iterable):
        show_iterable(*args, **kwargs)
    elif isinstance(first_arg, Image):
        show_image(first_arg)
