from flask import Blueprint, request, Response, send_file
from services import engine
from services.engine import get_book_by_id
import json
from services import db
from services.constant import COVER_PATH, BOOK_SAVE_PATH, TEMP_PATH
import uuid
import os
from flask_cors import CORS


bp = Blueprint('api', __name__)
CORS(bp, resources={r"/*": {"origins": "/api/content"}})


@bp.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, X-Requested-With, Content-Type, Accept, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD'
    response.headers['Access-Control-Expose-Headers'] = '*'
    return response


@bp.route('/api/add', methods=['POST'])
def add_book():
    file_type = request.form.get('file_type', None)
    if file_type is not None:
        if file_type == 'epub':
            file = request.files['file']
            save_path = os.path.join(BOOK_SAVE_PATH, 'epub_book')
            if not os.path.exists(save_path):
                os.mkdir(save_path)
            file_path = os.path.join(BOOK_SAVE_PATH, 'epub_book', str(uuid.uuid1()) + '.epub')
            file.save(file_path)
            return engine.ComicCrawler.start(crawler_name='epub_crawler', path=file_path)
        elif file_type == 'default_txt':
            file = request.files['file']
            title = file.filename.split('.')[-2]
            save_path = os.path.join(BOOK_SAVE_PATH, 'txt_book')
            if not os.path.exists(save_path):
                os.mkdir(save_path)
            file_path = os.path.join(BOOK_SAVE_PATH, 'txt_book', str(uuid.uuid1()) + '.txt')
            file.save(file_path)
            return engine.ComicCrawler.start(crawler_name='default_txt_crawler', path=file_path, title=title)
        elif file_type == 'ehentai_zip':
            file = request.files['file']
            title = file.filename.split('.')[-2]
            save_path = os.path.join(TEMP_PATH, f"{title}.zip")
            file.save(save_path)
            return engine.ComicCrawler.start(crawler_name='ehentai_zip_crawler', path=save_path)

    else:
        return engine.ComicCrawler.start(**request.json)


@bp.route('/api/get_crawler_progress', methods=['POST'])
def get_progress():
    if 'crawler_id' in request.json:
        return engine.ComicCrawler.get_current_progress(request.json['crawler_id'])
    else:
        return json.dumps({
            "msg": "params error"
        })


@bp.route('/api/content', methods=['POST', 'OPTIONS'])
def get_book_content():
    if request.method == 'OPTIONS':
        return {'msg': 'ok'}
    data = request.json
    content, mimetype = engine.BookContent.process(**data)
    if mimetype.startswith('path'):
        name = mimetype.split('/')[-1]
        return send_file(content, attachment_filename=name)
    else:
        return Response(content, mimetype=mimetype)


@bp.route('/api/info', methods=['POST'])
def get_book_info():
    try:
        book_id = request.json['book_id']
        book = get_book_by_id(int(book_id))
        if book:
            authors = []
            for author in book.authors:
                authors.append({
                    "name": author.name,
                    "picture": author.picture,
                    "description": author.description,
                    "is_stared": author.is_stared
                })
            tags = []
            for tag in book.tags:
                tags.append(tag.name)
            publishers = [publisher.name for publisher in book.publishers]
            series = []
            for my_series in book.series:
                series.append({
                    "name": my_series.name,
                    "description": my_series.description
                })
            msg = {
                'status': 'ok',
                'book_id': book.book_id,
                'title': book.title,
                'published': str(book.published),
                'publishers': publishers,
                'identifiers': book.identifiers,
                'language': book.languages,
                'series_id': book.series_id,
                'authors': authors,
                'description': book.description,
                'rating': book.rating,
                'cover_name': os.path.split(book.cover)[1],
                'last_modified': str(book.last_modified),
                'is_read': book.is_read,
                'is_stared': book.is_stared,
                'source': book.source,
                'uuid': book.uuid,
                'args': book.args,
                'content_info': json.loads(book.content_info),
                'file_type': book.file_type,
                'tags': tags,
                'series': series
            }
        else:
            msg = {
                'status': 'error'
            }
        return json.dumps(msg)
    except:
        return '1'


@bp.route('/api/cover/<cover_name>', methods=['GET'])
def get_cover(cover_name):
    # print(os.path.join(COVER_PATH, cover_name))
    file_path = os.path.abspath(os.path.join(COVER_PATH, cover_name))
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        raise FileNotFoundError


@bp.route('/api/list', methods=['POST'])
def get_list_query():
    params = request.json
    books = []
    if 'query' not in params:
        return json.dumps({'msg': 'invalid query'})
    if params['query'] == 'time':
        if 'page' not in params:
            return json.dumps({'msg': 'invalid page number'})
        books = db.BookListQuery.get_books_by_time(page=int(params['page']))
    elif params['query'] == 'author':
        if 'matcher' not in params:
            return json.dumps({'msg': 'invalid author name'})
        if 'page' not in params:
            return json.dumps({'msg': 'invalid page number'})
        if 'fuzzy' in params and params['fuzzy']:
            books = db.BookListQuery.get_books_by_like_author(page=int(params['page']), auther_name=params['matcher'])
        else:
            books = db.BookListQuery.get_books_by_author(page=int(params['page']), auther_name=params['matcher'])
    elif params['query'] == 'title':
        if 'matcher' not in params:
            return json.dumps({'msg': 'invalid book name'})
        if 'fuzzy' in params and params['fuzzy']:
            books = db.BookListQuery.get_books_by_like_name(page=int(params['page']), book_name=params['matcher'])
        else:
            books = db.BookListQuery.get_books_by_name(page=int(params['page']), book_name=params['matcher'])
    elif params['query'] == 'series':
        if 'matcher' not in params:
            return json.dumps({'msg': 'invalid series name'})
        if 'fuzzy' in params and params['fuzzy']:
            books = db.BookListQuery.get_books_by_like_series(page=int(params['page']), series_name=params['matcher'])
        else:
            books = db.BookListQuery.get_books_by_series(page=int(params['page']), series_name=params['matcher'])
    elif params['query'] == 'tag':
        if 'matcher' not in params:
            return json.dumps({'msg': 'invalid tag name'})
        if 'fuzzy' in params and params['fuzzy']:
            books = db.BookListQuery.get_books_by_like_tag(page=int(params['page']), tag_name=params['matcher'])
        else:
            books = db.BookListQuery.get_books_by_tag(page=int(params['page']), tag_name=params['matcher'])
    book_list = []
    for book in books:
        book_info = {
            'title': book.title,
            'book_id': book.book_id,
            'cover': book.cover.split('/')[-1],
            'authors': [author.name for author in book.authors],
            'series': [series.name for series in book.series]
        }
        book_list.append(book_info)
    return json.dumps(book_list)


@bp.route('/api/update', methods=['POST'])
def _update_book():
    book_id = request.form.get('book_id', None)
    if book_id:
        if 'file' not in request.files:
            return {'msg': 'error'}
        file = request.files['file']
        cover_name = str(uuid.uuid1()) + '.' + file.filename.split('.')[-1]
        file_path = os.path.join(COVER_PATH, cover_name)
        file.save(file_path)
        if db.UpdateBookInfoQuery.update_cover(file_path=file_path, book_id=int(book_id)):
            return json.dumps({'msg': 'ok', 'cover_name': cover_name})
        else:
            return json.dumps({'msg': 'error'})
    else:
        params = request.json
        if 'book_id' not in params:
            return {'msg': 'error'}
        db.UpdateBookInfoQuery.update_info(**params)
        return {'msg': 'ok'}


@bp.route('/api/adapters', methods=["POST"])
def _get_adapters():
    adapter_list = [{'label': engine.BookContent.adapter_translate(adapter_name),
                     'value': adapter_name}
                    for adapter_name in engine.BookContent.get_register_adapters()]
    return json.dumps(adapter_list)


@bp.route('/api/delete', methods=["post"])
def _delete_book():
    params = request.json
    if 'book_id' in params:
        status = db.delete_book(int(params['book_id']))
        if status:
            return {'msg': 'ok'}
        else:
            return {'msg': 'fail'}
    return {'msg': 'error'}


