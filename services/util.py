# from services import logger


# log = logger.create_logger()

to_run_list = []


class TestDecorator:
    def __init__(self, f):
        to_run_list.append(f)


@TestDecorator
def test():
    print('1')


@TestDecorator
def test2():
    print('2')


