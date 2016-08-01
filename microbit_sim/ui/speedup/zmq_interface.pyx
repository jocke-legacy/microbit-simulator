import asyncio
from microbit_sim.bus import AsyncBus

cpdef const char[:] LED_TYPE_PIXEL  b'pixel'
cpdef const char[:] LED_TYPE_DISPLAY  b'display'

cdef class CZMQUIInterface:
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.bus = AsyncBus()
        self.tasks = []

    cpdef create_task(self, coro):
        self.tasks.append(coro)
        task = self.loop.create_task(coro)

        def on_done(future):
            self.tasks.remove(coro)
            cdef Exception exc = future.exception()
            if exc:
                raise exc


    cdef start_listening(self):
        self.loop.call_later(1, self.refresh_stats)

        self.create_task(self.listen_leds())
        #self.add_task(self.receive_control_messages())
        #self.create_task(self.receive_display_updates())
        #self.create_task(self.refresh_ui())
        #self.print_tasks()

        #self.loop

    async def listen_leds(self):
        message_type, message_data = await self.bus
        if message_type == LED_TYPE_DISPLAY:
            pass

class ZMQUIInterface(CZMQUIInterface):
    pass
