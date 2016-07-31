from abc import ABCMeta, abstractmethod, abstractproperty
from typing import T


class Button(metaclass=ABCMeta):
    @abstractmethod
    def get_presses(self) -> int: pass

    @abstractmethod
    def is_pressed(self) -> bool: pass

    @abstractmethod
    def was_pressed(self) -> bool: pass

    @abstractmethod
    def _press(self): pass

    @abstractmethod
    def _down(self): pass

    @abstractmethod
    def _up(self): pass


class ImageData(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, width: int=5, height: int=5): pass

    @abstractmethod
    def get_pixel(self, x: int, y: int) -> int: pass

    @abstractmethod
    def set_pixel(self, x: int, y: int, value: int): pass

    @abstractmethod
    def __str__(self) -> str: pass

    @abstractmethod
    def copy(self: T) -> T: pass

    @abstractmethod
    def _repr_str(self) -> str: pass

    @abstractmethod
    def _set_from_string(self, string): pass


class Display(ImageData):
    @abstractmethod
    def scroll(self): pass

    @abstractmethod
    def show(self): pass
