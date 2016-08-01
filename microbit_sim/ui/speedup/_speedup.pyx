import curses
cimport curses

import numpy as np
from microbit_sim.renderer import common
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
