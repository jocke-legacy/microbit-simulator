import asyncio
import pyximport; pyximport.install()
import zmq.asyncio

from microbit_sim.logging import configure_logging
from microbit_sim.ui.asynciocurses import AsyncIOCursesUI
from microbit_sim.ui import common

configure_logging(filename='/tmp/microbit-renderer.log')

try:
    #loop = zmq.asyncio.ZMQEventLoop()
    #asyncio.set_event_loop(loop)
    AsyncIOCursesUI().run()
finally:
    common.end_curses()
