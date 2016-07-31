import logging
import logging.handlers

import colorlog
import zmq
import zmq.log.handlers
from microbit_sim import conf


def configure_logging(queue=None, filename='/tmp/microbit.log'):
    logging.basicConfig(level=conf.LOGGING_LEVEL, filename=filename)

    root_logger = logging.getLogger()
    stream_handler = root_logger.handlers[0]
    stream_handler.setFormatter(
        colorlog.ColoredFormatter(
            '%(log_color)s%(levelname)s:%(name)s:%(message)s'))

    if queue is not None:
        queue_handler = logging.handlers.QueueHandler(queue)
        root_logger.addHandler(queue_handler)

    # zmq_handler = zmq.log.handlers.PUBHandler(conf.LOGGING_PUB_SOCKET)
    # zmq_handler.setLevel(conf.LOGGING_LEVEL)
    # root_logger.addHandler(zmq_handler)

