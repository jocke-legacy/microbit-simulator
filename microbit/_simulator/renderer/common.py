import numpy as np

U_BLACK_SQUARE = '\u25A0'  # ■ BLACK SQUARE
U_FULL_BLOCK = '\u2588'  # █ FULL BLOCK
U_LOWER_HALF_BLOCK = '\u2584'  # ▄ LOWER HALF BLOCK
BRIGHTNESS_UNICODE_BLOCK = [
    ' ',  # 0
    '▁',  # 1
    '▁',  # 2  (duplicate of 1)
    '▂',  # 3
    '▃',  # 4
    '▄',  # 5
    '▅',  # 6
    '▆',  # 7
    '▉',  # 8
    '█',  # 9
]
BRIGHTNESS = BRIGHTNESS_UNICODE_BLOCK

BRIGHTNESS_8BIT = np.linspace(0, 255, num=10, dtype=int)

def ansi_brightness(value):
    return '\x1b[38;2;{red};0;0m'.format(red=BRIGHTNESS_8BIT[value])


def format_brightness(value, char=U_LOWER_HALF_BLOCK):
    return '{}{char}\x1b[0m'.format(
        ansi_brightness(value),
        char=char)

BRIGHTNESS_8BIT_ANSI = [format_brightness(value) for value in range(0, 10)]
