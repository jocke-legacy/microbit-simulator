from abc import ABCMeta, abstractmethod, abstractproperty, abstractclassmethod


class BaseEvent(metaclass=ABCMeta):

    @abstractmethod
    def pack(self):
        pass

    @abstractclassmethod
    def unpack(cls, packed):
        pass
