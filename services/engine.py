from functools import wraps
from typing import Dict, Any, Type, List
from collections import defaultdict
from services import logger
from services.exception import NoContentAdapterError, NoFileTypeError
from concurrent.futures import ThreadPoolExecutor, Future
from services.db import get_book_by_id, Book
import uuid
import time
import abc
from flask import render_template

log = logger.create_logger('Engine')


class CDBEngine:
    pass


class BookInfoModule:
    """Base class of book information display"""

    def __repr__(self):
        return "BookInfoModule"

    def __str__(self):
        return self.__repr__()

    def __init__(self):
        self.id = 1

    book_info_adapters = {}
    """
        Stores adapters that display specific type of book file
    """

    @classmethod
    def handle(cls, file_type: str):
        """
        Register adapters for for different book types like 'txt'
        'default' for the default book adapter
        :param file_type:
        :return:
        """
        def _handle(func):
            cls.book_info_adapters[file_type] = func
            log.info(f'{file_type} book info display adapter loading successful')

            @wraps(func)
            def wrapper(*args, **kwargs):
                rs = func(*args, **kwargs)
                return rs

            return wrapper

        return _handle

    @classmethod
    def process(cls, file_type: str, *args, **kwargs):
        """Chose adapter from book_info_adapters, if not find, use default adapter"""
        if file_type in cls.book_info_adapters:
            return cls.book_info_adapters[file_type](*args, **kwargs)
        else:
            log.warning(f'No book info adapter found for {file_type}! Use default adapter')
            return cls.book_info_adapters['default']()


class BookContent:
    """
    Used to process book_content requests, calls content adapter to handle the requests
    For example return a page of comic when requests book id, chapter number, page number
    """
    book_content_adapters = {}

    @classmethod
    def handle(cls, file_type: str):
        """Register adapter to process book content requests"""

        def _handle(func):
            cls.book_content_adapters[file_type] = func
            log.info(f'{file_type} book content display adapter loading successful')

            @wraps(func)
            def wrapper(*args, **kwargs):
                rs = func(*args, **kwargs)
                return rs

            return wrapper

        return _handle

    @classmethod
    def process(cls, file_type: str = '', *args, **kwargs) -> (bytes, str):
        """Choose adapter from book_info_adapters, if not find, raise exception"""
        if 'book_id' in kwargs:
            book = get_book_by_id(kwargs['book_id'])
            file_type = book.file_type
        else:
            book = None
        if not file_type:
            log.error('No file type provided, can not find proper adapter')
            raise NoFileTypeError
        if file_type in cls.book_content_adapters:
            return cls.book_content_adapters[file_type](book=book, *args, **kwargs)
        else:
            log.error(f'No adapter found for {file_type}! please check the log that if load the correct plugin')
            raise NoContentAdapterError


class ComicDownloader:
    """Default comic downloader, used to download book from Internet or convert save file to database"""
    executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix='downloader_')
    current_downloaders = []

    def __init__(self, name):
        self.result = None
        self.name = name
        self.future = None
        self.current_downloaders.append('name')

    @classmethod
    @abc.abstractmethod
    def get_info(cls) -> dict:
        return {
            'downloader_name': '',
            'file_type': ''
        }

    @abc.abstractmethod
    def extract_book(self, *args, **kwargs) -> any:
        """
        Every downloader should implement this function,
        it will be submitted to the tread pool after user start a download / extract
        """
        ...

    def start(self, *args, **kwargs):
        downloader = self.executor.submit(self.extract_book, *args, **kwargs)
        downloader.add_done_callback(self.call_back)
        self.future = downloader

    def call_back(self, future: Future):
        """Something you want to do after downloading complete"""
        log.debug(f'Downloader {self.name} complete')
        self.result = future.result()
        self.insert_book(result=self.result)

    @abc.abstractmethod
    def insert_book(self, result):
        pass


class ComicCrawler:
    """
    Every Crawler should inherited from this class, which is used to crawl book page by page
    """
    registered_downloader = {}
    executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix='crawler_')
    """"""
    def __del__(self):
        del self.registered_downloader[self.uuid]

    def __init__(self, name):
        self.name = name
        self.uuid = str(uuid.uuid1())
        self.registered_downloader[self.uuid] = self
        self.progress_display = f'Crawler: {self.name} initializing...'
        self.crawl_list = []
        self.book = None
        """book"""
        self.result = None

    def update_progress(self, info) -> None:
        """A method to update current crawler status, it may be displayed on the outer web"""
        self.progress_display = info

    @abc.abstractmethod
    def get_book_info(self, *args, **kwargs) -> dict:
        pass

    @abc.abstractmethod
    def can_crawl(self, book: Book) -> [bool, dict]:
        """
        A method to check if the book can be updated,
        if you want to update something,
        save the updates to crawl_list then return book_info
        else,
        keep the method return False
        """
        pass

    def update_book(self, book: Book) -> dict:
        pass

    @abc.abstractmethod
    def insert_book(self, result: dict):
        """Callback of _crawl or _update_crawl then insert a book to database"""
        pass

    @abc.abstractmethod
    def _crawl(self, crawl_info: dict) -> dict:
        """Crawl a page or a chapter"""
        pass

    @abc.abstractmethod
    def crawl(self, future: Future):
        """
        This method is the callback of get_book_info
        No IO operation allowed in this method!
        It should be handled by crawl_part and  be committed to the tread pool
        """
        pass

    def update_crawl(self, book_info):
        """
        This method is the callback of can_crawl
        No IO operation allowed in this method!
        It should be handled by crawl_part and  be committed to the tread pool
        """
        pass

    def _update_crawl(self, book_info: dict):
        pass

    def crawl_new_book(self, *args, **kwargs):
        """Entry of crawling book from Internet"""
        crawler = self.executor.submit(self.get_book_info, *args, **kwargs)
        crawler.add_done_callback(self.crawl)


