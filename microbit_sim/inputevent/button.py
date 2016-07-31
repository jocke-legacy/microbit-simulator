from .base import BaseEvent


class ButtonEvent(BaseEvent):
    __slots__ = (
        'name',
        'type'
    )

    def __init__(self, name, input_type):
        self.name = name
        self.type = input_type

    def pack(self):
        return self.name, self.type

    @classmethod
    def unpack(cls, packed):
        return cls(*packed)
