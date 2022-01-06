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


log = logger.create_logger('ehentai_adapter')


def generate_valid_path(parent_path: str, file_name: str) -> str:
    file_name = file_name.replace('/', ' ').replace('\\', ' ')
    file_name_part = file_name.split(' ')
    final_index = len(file_name_part)
    while True:
        current_path = os.path.join(parent_path, ' '.join(file_name_part[:final_index]))
        current_length = len(current_path)
        if current_length < 248:
            if len(' '.join(file_name_part[:final_index])) < 10:
                current_path += str(int(random.random() * 1000000))
            return current_path
        final_index -= 1


class EHentaiZipDownloader(DefaultZipDownloader):
    def get_book_info_from_file_name(cls, file_name: str, file_path: str = '') -> dict:
        author = re.search('\[(.*?)\((.*?)\)\]', file_name)
        if author:
            tag_author = author.group()
            author = re.search('\((.*?)\)', tag_author)
            if author:
                author = author.group()
                tags = [tag_author.replace(author, '').replace('(', '').replace(')', '').replace('[', '').replace(']',
                                                                                                                  '').strip()]
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
    @classmethod
    def get_name(cls):
        return 'ehentai_crawler'

    my_header = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }

    @staticmethod
    def e_hentai_crawler(cls, url):
        html = requests.get(url, headers=cls.my_header)
        dom = etree.HTML(html.text)
        title = dom.xpath('//h1[@id="gn"]/text()')[0]
        left_list = dom.xpath('//div[@id="gdd"]/table/*')
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
        ehentai_info_dict['tag_dict'] = tag_dict
        if 'artist' in tag_dict:
            author = tag_dict['artist']
            print(author)
        else:
            author = ''
        cover_url = dom.xpath('//div[@id="gd1"]/div/@style')[0].split(' ')[-2][4:-1]
        log.debug(f'Successfully crawled URL:{url}')
        return {
            'title': title,
            'published': published,
            'languages': languages,
            'rating': rating,
            'length': length,
            'cover': cover_url,
            'source': url,
            'author_name': author,
            'e_hentai_info': ehentai_info_dict
        }

    def crawl(self, future: Future):
        book_info = future.result()
        if 'msg' in book_info and book_info['msg'] == 'fail':
            log.error('Fail to attach book info')
            raise ValueError
        cover_img = requests.get(book_info['cover'], headers=self.my_header)

        cover_uuid = str(uuid.uuid1())
        cover_url = book_info['cover']
        book_info['cover'] = os.path.join(COVER_PATH, f"{cover_uuid}.{cover_url.split('.')[-1]}")
        with open(book_info['cover'], 'wb') as f:
            f.write(cover_img.content)
        page_max: int = book_info['length'] // 40 + 1
        book_folder_url = generate_valid_path(os.path.abspath(os.path.join('data', 'books', 'ehentai_comic')),
                                              book_info['title'])
        try:
            os.mkdir(book_folder_url)
        except FileNotFoundError as e:
            try:
                os.mkdir(os.path.join('data', 'books', 'ehentai_comic'))
                os.mkdir(book_folder_url)
            except FileExistsError:
                os.mkdir(book_folder_url)

        except FileExistsError:
            pass
        image_path_list = []
        image_url_list = []
        img_index = 1
        for page in range(page_max):
            time.sleep(0.84)
            html = requests.get(f'{book_info["source"]}?p={page}', headers=self.my_header)
            dom = etree.HTML(html.text)
            for content_page in dom.xpath('//div[@id="gdt"]')[0][:-1]:
                page_url = content_page[0][0].get('href')
                file_page = requests.get(page_url, headers=self.my_header)
                image_dom = etree.HTML(file_page.text)
                image_url = image_dom.xpath('//div[@id="i3"]/a/img')[0].get('src')
                image = requests.get(image_url, headers=self.my_header)
                new_image_path = os.path.join(book_folder_url, str(img_index) + '.' + image_url.split('.')[-1])
                with open(new_image_path, 'wb') as f:
                    f.write(image.content)
                img_index += 1
                image_path_list.append(new_image_path)
                image_url_list.append(image_url)
                log.debug(f'Crawl succeed: {new_image_path}')
                self.update_progress(
                    f'Now crawling {img_index - 1}/{book_info["length"]}({round((img_index - 1) / book_info["length"] * 100)}%)')
                time.sleep(0.5)
        book_info['url'] = book_folder_url
        book_info['args'] = {
            'page_path_list': image_path_list,
            'image_url_list': image_url_list
        }
        book_info['e_hentai_info']['page_number']=len(image_path_list)
        self.insert_book(book_info)

    def get_book_info(self, *args, **kwargs) -> dict:
        if 'url' in kwargs:
            return self.e_hentai_crawler(self, url=kwargs['url'])
        else:
            log.error('No URL provided')
            return {'msg': 'fail'}
        pass

    def can_crawl(self, book: Book) -> [bool, dict]:
        return False

    def insert_book(self, result: dict):
        result['tags'] = []
        for tag_key in result['e_hentai_info']['tag_dict']:
            for tag_value in result['e_hentai_info']['tag_dict'][tag_key]:
                result['tags'].append(tag_value)
        result['file_type'] = 'ehentai_comic'
        result['args'] = json.dumps(result['e_hentai_info'])
        result['content_info'] = json.dumps([{"name": f"共{result['e_hentai_info']['page_number']}页", "chapters": [{"name": f"第{x+1}页"} for x in range(result['e_hentai_info']['page_number'])]}])
        add_new_book(**result)
        self.is_complete = True
        pass


@BookContent.handle('ehentai_comic')
def ehentai_comic_handler(page: str, book: Book, *args, **kwargs) -> (bytes, str):
    log.debug(f'Process {book.title}: page: {page}')
    if book:
        eh_info = json.loads(book.args)
        if os.path.exists(book.url):
            with open(os.path.join(book.url, eh_info['page_path_list'][int(page)]), 'rb') as f:
                return f.read(), 'image/jpeg'
        else:
            raise FileNotFoundError
    else:
        raise BookExistError


# test_default_zip_downloader = EHentaiZipDownloader('test')
# test_default_zip_downloader.start(file_path='data/[pecon (Kino)] Dokidoki Ichaicha Fuwafuwa   心神難寧, 恩恩愛愛, 輕飄飄 (Puella Magi Madoka Magica Side Story_ Magia Record) [Chinese] [Digital]-1280x.zip')

# BookContent.process(file_type='default_zip', page=2, book=get_book_by_id(1))

# test_crawler = EhentaiCrawler('test_crawler')
# test_crawler.crawl_new_book(url='https://e-hentai.org/g/2040421/17f346afc1/')
