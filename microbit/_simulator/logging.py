import logging

import colorlog
import zmq
import zmq.log.handlers

from microbit._simulator import conf


def configure_logging():
    logging.basicConfig(level=conf.LOGGING_LEVEL)
    zmq_handler = zmq.log.handlers.PUBHandler(conf.LOGGING_PUB_SOCKET)
    zmq_handler.setLevel(conf.LOGGING_LEVEL)
    # zmq_handler.setFormatter(
    #     colorlog.ColoredFormatter(
    #         '%(log_color)s%(levelname)s:%(name)s:%(message)s'))

    root_logger = logging.getLogger()
    #root_logger.addHandler(zmq_handler)
    root_logger.handlers = [zmq_handler]

