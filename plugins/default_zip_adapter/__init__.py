from services import logger
from services.engine import ComicDownloader, BookContent
from services.exception import FileExtendNotMatchError, BookExistError
from services.db import add_new_book, get_book_by_id, Book
from services.constant import COVER_PATH
import os
import zipfile
import uuid
import json

log = logger.create_logger('default_zip')


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