from concurrent.futures._base import Future

from PIL.Image import Image
from services import logger
from .config import data
from services.engine import BookInfoModule, ComicDownloader, BookContent, ComicCrawler
from services.exception import FileExtendNotMatchError, BookExistError
from services.db import add_new_book, get_book_by_id, Book
from PIL import Image
import time
import re
from services.constant import COVER_PATH
import os
import zipfile
import requests
from lxml import etree
import uuid
import json
from datetime import datetime

log = logger.create_logger('test')


@BookInfoModule.handle('default_zip')
def hello_world():
    return 'Hello World'


class DefaultZipDownloader(ComicDownloader):
    """A Adapter that can extract basic info from zip compressed file"""

    @classmethod
    def get_info(cls) -> dict:
        return {
            'downloader_name': 'Default Zip Downloader',
            'file_type': 'default_zip'
        }

    @classmethod
    def get_cover_name(cls, file_name_list: list) -> str:
        return file_name_list[0]

    @classmethod
    def get_book_info_from_file_name(cls, file_name: str, file_path: str = '') -> dict:
        return {
            'title': file_name,
            'source': 'Default Zip Downloader',
            'file_type': 'default_zip'
        }

    def extract_book(self, *args, **kwargs) -> any:
        if 'file_path' in kwargs:
            path, file_fullname = os.path.split(kwargs['file_path'])
            filename, extend = os.path.splitext(file_fullname)
            if extend == '.zip':
                book_info = self.get_book_info_from_file_name(filename, kwargs['file_path'])
                book_info['url'] = kwargs['file_path']
                my_zip = zipfile.ZipFile(kwargs['file_path'])
                file_list = my_zip.namelist()
                cover_file_name = self.get_cover_name(file_list)
                cover_extend = cover_file_name.split('.')[-1]
                cover_uuid = str(uuid.uuid1())
                book_info['cover'] = os.path.join(COVER_PATH, f'{cover_uuid}.{cover_extend}')
                with my_zip.open(cover_file_name) as cover:
                    with open(book_info['cover'], 'wb') as f:
                        f.write(cover.read())
                    # image: Image = Image.open(book_info['cover'])
                    # small_cover: Image = image.resize((150, 225))
                    # small_cover.save(os.path.join(COVER_PATH, cover_uuid + f'_small.{cover_extend}'))
                content = file_list[1:]
                book_info['content_info'] = json.dumps(content)
                return book_info
            else:
                raise FileExtendNotMatchError
        else:
            raise FileNotFoundError

            pass

    def insert_book(self, result: dict):
        add_new_book(**result)


class EHentaiZipDownloader(DefaultZipDownloader):
    def get_book_info_from_file_name(cls, file_name: str, file_path: str = '') -> dict:
        author = re.search('\[(.*?)\((.*?)\)\]', file_name)
        if author:
            tag_author = author.group()
            author = re.search('\((.*?)\)', tag_author)
            if author:
                author = author.group()
                tags = [tag_author.replace(author, '').replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()]
                author = author.replace('(', '').replace(')', '')
            else:
                author = ''
                tags = []
        else:
            author = ''
            tags = []

        title = re.sub('\(.*?\)', '', file_name)
        title = re.sub('\[.*?\]', '', title)
        return {
            'title': title,
            'source': 'Ehentai Zip Downloader',
            'file_type': 'default_zip',
            'author_name': author,
            'tags': tags
        }


class EhentaiCrawler(ComicCrawler):

    def crawl(self, future: Future):
        re
        pass

    @staticmethod
    def e_hentai_crawler(url):
        my_header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        html = requests.get(url, headers=my_header)

        dom = etree.HTML(html.text)
        title = dom.xpath('//h1[@id="gn"]/text()')[0]
        left_list = dom.xpath('//div[@id="gdd"]/table/*')
        for para in left_list:
            print(f'{para[0].text}')
        ehentai_info_dict = {}
        published = datetime.strptime(left_list[0][1].text, '%Y-%m-%d %H:%M')
        languages = left_list[3][1].text.strip()
        length = int(left_list[-2][1].text.replace(' pages', ''))
        ehentai_info_dict['favorited'] = left_list[-1][1].text
        rating = float(dom.xpath('//td[@id="rating_label"]')[0].text.replace('Average: ', ''))
        tag_list = dom.xpath('//div[@id="taglist"]/table/*')
        tag_dict = {}
        for tag in tag_list:
            tag_name = tag[0].text[:-1]
            tag_content = []
            for content in tag[1]:
                tag_content.append(content[0].text)
            tag_dict[tag_name] = tag_content
        if 'artist' in tag_dict:
            author = tag_dict['artist']
        else:
            author = ''
        cover_url = dom.xpath('//div[@id="gd1"]/div/@style')[0].split(' ')[-2][4:-1]
        # cover_img = requests.get(cover_url, headers=my_header)

        # cover_uuid = str(uuid.uuid1())
        # cover_url =
        #
        # with open(os.path.join('data', 'cover', f"{cover_uuid}.{cover_url.split('.')[-1]}"), 'wb') as f:
        #     f.write(cover_img.content)
        log.debug(f'Successfully crawled URL:{url}')
        return {
            'title': title,
            'published': published,
            'languages': languages,
            'rating': rating,
            'cover': cover_url,
            'source': url,
            'author': author
        }

    def get_book_info(self, *args, **kwargs) -> dict:
        if 'url' in kwargs:
            return self.e_hentai_crawler(kwargs['url'])
        else:
            log.error('No URL provided')
            return {'msg': 'fail'}
        pass

    def can_crawl(self, book: Book) -> [bool, dict]:
        return False

    def insert_book(self, result: dict):
        add_new_book(**result)
        pass

    def _crawl(self, crawl_info: dict) -> dict:

        pass


@BookContent.handle('default_zip')
def default_zip_handler(page: int, book: Book, *args, **kwargs) -> (bytes, str):
    log.debug(f'Process {book.title}: page: {page}')
    if book:
        if os.path.exists(book.url):
            my_zip = zipfile.ZipFile(book.url)
            file_list = my_zip.namelist()
            with my_zip.open(file_list[int(page)]) as file:
                return file.read(), 'image/jpeg'
        else:
            raise FileNotFoundError
    else:
        raise BookExistError


# test_default_zip_downloader = EHentaiZipDownloader('test')
# test_default_zip_downloader.start(file_path='data/[pecon (Kino)] Dokidoki Ichaicha Fuwafuwa   心神難寧, 恩恩愛愛, 輕飄飄 (Puella Magi Madoka Magica Side Story_ Magia Record) [Chinese] [Digital]-1280x.zip')

# BookContent.process(file_type='default_zip', page=2, book=get_book_by_id(1))
