import logging


logging.basicConfig(
    filename='log/develop_debug.log',
    level=logging.DEBUG,
    format='[%(asctime)s][%(levelname)s][%(name)s]%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S, '
)


def create_logger(name):
    return logging.getLogger(name)