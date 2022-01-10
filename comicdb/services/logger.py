import logging
import os

if not os.path.exists('log'):
    os.mkdir('log')

logging.basicConfig(
    filename='log/comicdb.log',
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s][%(name)s]%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S, '
)


def create_logger(name):
    return logging.getLogger(name)