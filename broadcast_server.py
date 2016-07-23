import argparse
import logging
import json

import zmq

log = logging.getLogger(__name__)


def parse_args():
    arg_parser = argparse.ArgumentParser(
        description='Broadcast server for the microbit-simulator'
    )

    arg_parser.add_argument('--config', default='config.json')

    return arg_parser.parse_args()


def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.loads(f.read())


def main():
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()
    config = load_config(args.config)

    pub_port = config['broadcast']['pub_port']
    rep_port = config['broadcast']['rep_port']

    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind('tcp://*:{}'.format(pub_port))

    rep_socket = context.socket(zmq.REP)
    rep_socket.bind('tcp://*:{}'.format(rep_port))

    log.info('Listening...')
    while True:
        string = rep_socket.recv()
        log.info(string)
        pub_socket.send(string)


if __name__ == '__main__':
    main()
