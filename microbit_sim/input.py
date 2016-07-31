import curses
import logging
import select
import sys
import threading
import tty

import termios

import time

_log = logging.getLogger(__name__)

BUTTON_A = '\x1bD'  # LEFT ARROW
BUTTON_B = '\x1bC'  # RIGHT ARROW


def watch_input(win, fd, button_a, button_b, timeout=10):
    pass
    # while True:
    #     win.nodelay(True)
    #     ch = win.getch()
    #
    #     if ch == curses.KEY_LEFT:
    #         button_a._press()
    #     elif ch == curses.KEY_RIGHT:
    #         button_b._press()
    #
    #     time.sleep(0.1)

    #
    # previous_settings = tty.tcgetattr(fd.fileno())
    #
    # try:
    #     #tty.setraw(fd.fileno())
    #     while True:
    #         select.select([fd], [], [], 0)
    #
    #         first_b = fd.read(1)
    #
    #         if not first_b == '\x1b':
    #             _log.info('Unknown start: {!r}'.format(first_b))
    #             continue
    #
    #         second_b = fd.read(1)
    #         both = first_b + second_b
    #
    #         if both == BUTTON_A:
    #             button_a._press()
    #         elif both == BUTTON_B:
    #             button_b._press()
    #
    # finally:
    #     tty.tcsetattr(fd.fileno(), termios.TCSADRAIN, previous_settings)
