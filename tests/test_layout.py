from microbit._simulator.renderer.layout import Layout, Box, Direction


def test_vertical():
    layout = Layout(width=50, height=100)

    leds = Box('leds', width=5, height=5)

    microbit = Layout(Direction.VERTICAL, leds, height=10)

