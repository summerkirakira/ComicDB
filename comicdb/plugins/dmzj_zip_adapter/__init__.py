from concurrent.futures._base import Future
from services import logger
from services.engine import BookInfoModule, ComicDownloader, BookContent, ComicCrawler
from services.exception import FileExtendNotMatchError, BookExistError
from services.db import add_new_book, get_book_by_id, Book
import re
from services.constant import COVER_PATH
import os
import zipfile
from services import constant
import requests
from lxml import etree
import uuid
import time
from lxml import etree
import json
from datetime import datetime
import random
from ..default_zip_adapter import DefaultZipDownloader
import ebooklib
from dateutil.parser import parse
from ebooklib import epub


class DmzjZipCrawler(ComicCrawler):

    my_header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Referer': 'http://manhua.dmzj.com/'
    }

    @classmethod
    def chapter_order(cls, chapter):
        return chapter['chapter_order']

    @classmethod
    def get_name(cls):
        return 'dmzj_zip_crawler'

    def get_book_info(self, *args, **kwargs) -> dict:
        if 'path' not in kwargs:
            return {}
        book_uri = kwargs['path']
        with open(os.path.join(book_uri, 'inform.json'), 'r') as f:
            dmzj_info = json.loads(f.read())
        book_info = {
            "title": dmzj_info['title'],
            "cover": dmzj_info['cover'].replace('dmzj1', 'dmzj'),
            "description": dmzj_info['description'],
            'last_modified': datetime.fromtimestamp(dmzj_info['last_updatetime']),
            'published': datetime.fromtimestamp(dmzj_info['last_updatetime']),
            'tags': [tag['tag_name'] for tag in dmzj_info["types"]] + [status['tag_name'] for status in dmzj_info["status"]],
            'author_name': [author['tag_name'] for author in dmzj_info['authors']],
            'url': book_uri,
            'source': 'http://manhua.dmzj.com/',
            'dmzj_info': dmzj_info
        }
        book_info['tags'].append('动漫之家')
        book_info['file_type'] = 'dmzj_zip'
        return book_info

    def can_crawl(self, book: Book) -> [bool, dict]:
        return False

    def insert_book(self, result: dict):
        add_new_book(**result)
        self.is_complete = True
        self.update_progress('insert_complete')
        pass

    def crawl(self, future: Future):
        book_info = future.result()
        if not book_info:
            return
        book_cover = requests.get(book_info['cover'], headers=self.my_header)
        if book_cover.status_code == 200:
            with open(os.path.join(book_info['url'], 'cover.jpg'), 'wb') as f:
                f.write(book_cover.content)
            cover_path = os.path.join(COVER_PATH, f"{str(uuid.uuid1())}.jpg")
            with open(cover_path, 'wb') as f:
                f.write(book_cover.content)
            book_info['cover'] = cover_path
        else:
            book_info['cover'] = os.path.join(COVER_PATH, 'default_cover.jpg')
        content_info = []
        chapters = []
        for chapter in book_info['dmzj_info']['chapters'][0]['data']:
            chapters.append(chapter)
        chapters.sort(key=self.chapter_order)
        for chapter_info in chapters:
            chapter = {
                'name': chapter_info['chapter_title'],
                'update_time': chapter_info['chapter_title'],
            }
            with zipfile.ZipFile(os.path.join(book_info['url'], f'{chapter_info["chapter_title"]}-{chapter_info["chapter_id"]}.zip'), 'r') as my_zip:
                image_list = my_zip.namelist()
            chapter['chapters'] = [{
                'name': f"第{int(image_name.split('.')[-2]) + 1}页",
                'href': f'{chapter_info["chapter_title"]}-{chapter_info["chapter_id"]}/{image_name}'
            } for image_name in image_list]
            content_info.append(chapter)
        book_info['content_info'] = json.dumps(content_info)
        self.insert_book(book_info)


def compress_file(zipfilename, dirname):
    if os.path.isfile(dirname):
        with zipfile.ZipFile(zipfilename, 'w') as z:
            z.write(dirname)
    else:
        with zipfile.ZipFile(zipfilename, 'w') as z:
            for root, dirs, files in os.walk(dirname):
                for single_file in files:
                    if single_file != zipfilename:
                        filepath = os.path.join(root, single_file)
                        z.write(filepath, single_file)


@BookContent.handle('dmzj_zip')
def get_dmzj_content(book: Book, href: str, *args, **kwargs):
    if 'is_download' in kwargs and kwargs['is_download']:
        temp_file = os.path.abspath(os.path.join(constant.TEMP_PATH, book.uuid + '.zip'))
        compress_file(temp_file, book.url)
        return temp_file, f'path/{book.title}.zip'
    else:
        my_zip = zipfile.ZipFile(os.path.join(book.url, f"{href.split('/')[-2]}.zip"))
        with my_zip.open(href.split('/')[-1]) as file:
            return file.read(), 'image/jpeg'


if not os.path.exists(os.path.join('data', 'books', 'dmzj_book')):
    os.mkdir(os.path.join('data', 'books', 'dmzj_book'))