import curses
cimport curses
import asyncio

import numpy as np
import time
from microbit_sim.ui import common
cimport numpy as np

cdef render_output(pad, win, output_lines, output_layout):
    for i, line in enumerate(output_lines):
        pad.addstr(i + 1, 0, line)

    pad_min_y = max(len(output_lines))

cdef int c_led_x(int x):
    return x * 2 + 2

cdef int c_led_y(int y):
    return y + 1

def led_y(y):
    return c_led_y(y)

def led_x(x):
    return c_led_x(x)

cdef int COLOR_RANGE_START = common.CURSES_LED_COLOR_RANGE[0]

cdef int cy_pair_number_for_value(int value):
    return COLOR_RANGE_START + value

def pair_number_for_value(value):
    return cy_pair_number_for_value(value)

def render_leds(win,
                np.ndarray[np.uint8_t, ndim=2] buffer,
                int offset_y,
                int offset_x):
    for (y, x), value in np.ndenumerate(buffer):
        win.addch(offset_y + c_led_y(y),
                  offset_x + c_led_x(x),
                  common.U_LOWER_HALF_BLOCK,
                  curses.color_pair(cy_pair_number_for_value(value)))


def rate_limit(min_delta, callback=None):
    cdef int t_last = 0
    cdef int t_now, delta_t

    while True:
        t_now = time.time()
        delta_t = t_now - t_last

        if delta_t < min_delta:
            if callback is not None:
                callback(delta_t, min_delta)
            else:
                time.sleep(min_delta - delta_t)
            continue

        yield


class ratelimit:
    def __init__(self, float min_delta):
        cdef float t_last = 0
        self.t_last = t_last
        self.min_delta = min_delta

    def __aiter__(self):
        return self

    async def __anext__(self):
        t_now = time.time()
        cdef float t_delta = t_now - self.t_last

        if t_delta < self.min_delta:
            await asyncio.sleep(self.min_delta - t_delta)

        self.t_last = t_now
        return t_now
