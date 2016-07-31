import time
import logging
import functools
import sys
from datetime import timedelta

import zmq

_log = logging.getLogger(__name__)


def retry(interval=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    _log.exception('Failed, retrying in %s',
                                   timedelta(seconds=interval))
                    time.sleep(interval)

        return wrapper

    return decorator


@retry()
def listen_and_print(address):
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.setsockopt_string(zmq.SUBSCRIBE, '')
    sub.connect(address)

    while True:
        print(sub.recv_string())


if __name__ == '__main__':
    listen_and_print(sys.argv[1])
