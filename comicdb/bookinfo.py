from flask import Blueprint, request
from services import engine, db


bp = Blueprint('info', __name__)


@bp.route('/info/book/<book_id>', methods=('GET', 'POST'))
def info_page(book_id):
    book_id = int(book_id)
    book = db.get_book_by_id(book_id)
    return engine.BookInfoModule.process('default_zip', book=book)

