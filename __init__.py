__package__ = "comicdb"
import datetime
from services.db import create_all_db, add_new_book, get_author_by_id, update_book_info
from services import engine
import os
from flask import Flask
from services import logger
log = logger.create_logger('main')


# create_all_db()
# book = add_new_book(
#     title='魔法少女小圆脸',
#     publisher_name='芳文社',
#     author_name='虚渊玄',
#     identifiers='uuid:24341232423412',
#     languages='zho',
#     description='小圆的故事',
#     cover='cover/madoka.png',
#     rating=5.0,
#     source='Internet',
#     file_type='epub',
#     url='/document'
#     )

# test = update_book_info(
#     book_id=1,
#     title='魔法少女小圆脸',
#     publisher_name='芳文社dsg',
#     author_name='虚渊玄sd大',
#     identifiers='uuid:24341232423412',
#     languages='zho',
#     description='小圆的故事sd',
#     cover='cover/madokasd.png',
#     rating=5.0,
#     source='Internet',
#     file_type='epub',
#     url='/document...'
#     )


class Platform:
    def __init__(self):
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        for folder_name in os.listdir("plugins"):
            if not folder_name.startswith('.'):
                self.run_plugin(module_name=folder_name)

    def run_plugin(self, module_name: str):
        plugin = __import__(f"plugins.{module_name}", fromlist=["__init__"])
        log.info(f"module [{module_name}] import successfully")
        self.plugins.append(plugin)


create_all_db()
platform = Platform()
# log.debug('Platform start successful')
# print(engine.ComicCrawler.start(crawler_name='ehentai_crawler', url='https://e-hentai.org/g/2086988/a340834391/'))

