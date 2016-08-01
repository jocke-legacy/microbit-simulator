import pyximport; pyximport.install()
import curses

from microbit_sim.logging import configure_logging
from microbit_sim.ui.asynciocurses import AsyncIOCursesUI

configure_logging(filename='/tmp/microbit-renderer.log')

try:
    AsyncIOCursesUI().run()
finally:
    if not curses.isendwin():
        curses.endwin()
