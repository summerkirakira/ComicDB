from concurrent.futures._base import Future
from services import logger
from services.engine import BookInfoModule, ComicDownloader, BookContent, ComicCrawler
from services.exception import FileExtendNotMatchError, BookExistError
from services.db import add_new_book, get_book_by_id, Book
import re
from services.constant import COVER_PATH
import os
import zipfile
import requests
from lxml import etree
import uuid
import time
import json
from datetime import datetime
import random
from ..default_zip_adapter import DefaultZipDownloader
import ebooklib
from dateutil.parser import parse
from ebooklib import epub

class EpubCrawler(ComicCrawler):
    @classmethod
    def get_name(cls):
        return 'epub_crawler'

    def get_book_info(self, *args, **kwargs) -> dict:
        if 'path' in kwargs:
            book_info = {}
            book = epub.read_epub(kwargs['path'])
            book_info['title'] = book.get_metadata('DC', 'title')[0][0]
            book_info['author'] = book.get_metadata('DC', 'creator')[0][0]
            book_info['identifiers'] = book.get_metadata('DC', 'identifier')[0][0]
            try:
                book_info['publisher'] = book.get_metadata('DC', 'publisher')[0][0]
            except IndexError:
                book_info['publisher'] = ''
            try:
                book_info['description'] = book.get_metadata('DC', 'description')[0][0]
            except IndexError:
                book_info['description'] = ''
            try:
                book_info['languages'] = book.get_metadata('DC', 'language')[0][0]
            except IndexError:
                book_info['languages'] = ''
            try:
                book_info['published'] = book.get_metadata('DC', 'date')[0][0]
            except IndexError:
                book_info['published'] = ''
            try:
                cover_image = book.get_metadata('OPF', 'cover')[0][1]['content']
                cover_image = book.get_item_with_id(cover_image)
                cover = cover_image
            except IndexError:
                cover = None
            book_info['cover'] = cover
            book_info['url'] = kwargs['path']
            print(book_info)
            return book_info
        else:
            raise ValueError

    def can_crawl(self, book: Book) -> [bool, dict]:
        return False

    def insert_book(self, result: dict):
        add_new_book(**result)
        self.is_complete = True
        self.update_progress('insert_complete')
        pass

    def crawl(self, future: Future):
        book_info = future.result()
        if book_info['cover']:
            cover_id = str(uuid.uuid1())
            cover_extend = book_info['cover'].get_name().split('.')[-1]
            with open(os.path.join(COVER_PATH, f'{cover_id}.{cover_extend}'), 'wb') as f:
                f.write(book_info['cover'].get_content())
            book_info['cover'] = os.path.join(COVER_PATH, f'{cover_id}.{cover_extend}')
        else:
            book_info['cover'] = os.path.join(COVER_PATH, 'default_cover.jpg')
        book_info['file_type'] = 'default_epub'
        book_info['source'] = 'epub_crawler'
        if book_info['published']:
            book_info['published'] = parse(book_info['published'])
        else:
            del book_info['published']
        self.insert_book(book_info)
        self.update_progress('crawl complete')
