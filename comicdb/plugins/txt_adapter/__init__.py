from concurrent.futures._base import Future
from services.engine import BookInfoModule, ComicDownloader, BookContent, ComicCrawler
from services.db import add_new_book, get_book_by_id, Book
import os
import json


class DefaultTxtCrawler(ComicCrawler):
    @classmethod
    def get_name(cls):
        return 'default_txt_crawler'

    def get_book_info(self, *args, **kwargs) -> dict:
        if 'path' in kwargs:
            book_info = {
                'title': kwargs['title'],
                'url': kwargs['path'],
                'cover': 'default_cover.jpg'
            }
            return book_info

    def can_crawl(self, book: Book) -> [bool, dict]:
        return False

    def insert_book(self, result: dict):
        add_new_book(**result)
        self.is_complete = True
        self.update_progress('insert_complete')

    def crawl(self, future: Future):
        book_info = future.result()
        book_info['content_info'] = json.dumps([{
            '正文': [{
                "name": "正文",
                "href": "content"
            }]
        }])
        book_info['file_type'] = "default_txt"
        self.insert_book(book_info)
        self.update_progress('crawl complete')


@BookContent.handle('default_txt')
def _upload_txt(book: Book, *args, **kwargs):
    if 'is_download' in kwargs and kwargs['is_download']:
        return os.path.abspath(book.url), f'path/{book.title}.txt'

