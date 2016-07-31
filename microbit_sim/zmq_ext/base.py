from abc import ABCMeta, abstractmethod

import numpy
import umsgpack
import zmq


class Socket(zmq.Socket, metaclass=ABCMeta):
    @abstractmethod
    def _func_wrapper(self, func, *args, **kwargs):
        pass

    def _recv_wrapper(self, *args, **kwargs):
        return self._func_wrapper(self.recv, *args, **kwargs)

    def _send_wrapper(self, *args, **kwargs):
        return self._func_wrapper(self.send, *args, **kwargs)

    def recv_msgpack(self, **kwargs):
        return umsgpack.unpackb(self._recv_wrapper(**kwargs))

    def send_msgpack(self, obj, **kwargs):
        return self._send_wrapper(umsgpack.packb(obj))

    def send_array(self, numpy_array, flags=0, copy=True, track=False):
        """send a numpy array with metadata"""
        metadata = dict(
            dtype=str(numpy_array.dtype),
            shape=numpy_array.shape,
        )
        return self.send_multipart([umsgpack.packb(metadata), numpy_array],
                                   flags=flags,
                                   copy=copy,
                                   track=track)

    def recv_array(self, flags=0, copy=True, track=False):
        """recv a numpy array"""
        multipart = self._func_wrapper(self.recv_multipart,
                                       flags=flags,
                                       copy=copy,
                                       track=track)
        metadata_bytes, msg = multipart
        metadata = umsgpack.unpackb(metadata_bytes)
        buf = memoryview(msg)
        numpy_array = numpy.frombuffer(buf, dtype=metadata['dtype'])
        return numpy_array.reshape(metadata['shape'])



