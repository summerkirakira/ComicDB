import os
from services import constant
from services.db import create_all_db


def remove_temp():
    temp_file_list = os.listdir(constant.TEMP_PATH)
    for file in temp_file_list:
        file_path = os.path.join(constant.TEMP_PATH, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def check_folder():
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists(constant.COVER_PATH):
        os.mkdir(constant.COVER_PATH)
    if not os.path.exists(constant.TEMP_PATH):
        os.mkdir(constant.TEMP_PATH)
    if not os.path.exists('database'):
        os.mkdir('database')
    if not os.path.exists('log'):
        os.mkdir('log')
    if not os.path.exists(os.path.join('cover', 'default_cover.jpg')):
        with open(os.path.join('comicdb', 'src', 'default_cover.jpg'), 'rb') as f:
            with open(os.path.join('data', 'cover', 'default_cover.jpg'), 'wb') as cover:
                cover.write(f.read())


def start():
    remove_temp()
    check_folder()
    create_all_db()

