import logging

_log = logging.getLogger(__name__)


class Button:
    def __init__(self, _name):
        self._name = _name
        self._presses = 0
        self._is_pressed = False

    def get_presses(self) -> int:
        """
        Get the number of presses since last time get_presses was called.

        If the button is currently pressed, it will be included.
        """
        presses = self._presses
        self._presses = 0
        return presses

    def was_pressed(self) -> bool:
        """
        Check if the button has been pressed since get_presses() was last run.
        """
        was_pressed = self._presses > 0
        self._presses = 0
        return was_pressed

    def is_pressed(self) -> bool:
        """
        Check if the button is currently pressed.
        """
        return self._is_pressed

    def __repr__(self):
        return '<{cls} {name!r} ' \
               'is_pressed={is_pressed!r} ' \
               'presses={presses!r}>'.format(cls=self.__class__.__name__,
                                             name=self._name,
                                             is_pressed=self._is_pressed,
                                             presses=self._presses)

    def _press(self):
        """
        Press and release the button instantly.
        """
        self._down()
        self._up()

    def _down(self):
        _log.debug('down: {}'.format(self))
        self._presses += 1
        self._is_pressed = True

    def _up(self):
        _log.debug('up: {}'.format(self))
        self._is_pressed = False
