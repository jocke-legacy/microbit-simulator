import umsgpack

from .base import BaseEvent
from .button import ButtonEvent

MSGPACK_EXT_EVENT_TYPE = {
    0x01: ButtonEvent,
}

# Switch keys and values
EVENT_TYPE_MSGPACK_EXT = dict(
    zip(*reversed(list(zip(*MSGPACK_EXT_EVENT_TYPE.items()))))
)


def pack(event: BaseEvent):
    ext = EVENT_TYPE_MSGPACK_EXT[type(event)]
    return umsgpack.packb(umsgpack.Ext(ext, event.pack()))


def unpack(ext: umsgpack.Ext):
    event_type = MSGPACK_EXT_EVENT_TYPE[ext.type]
    return event_type.unpack(ext.data)
