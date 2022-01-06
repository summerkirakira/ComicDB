from flask import Blueprint, request, Response, send_file
from services import engine
from services.engine import get_book_by_id
import json
from services import db
from services.db import Book
from services.constant import COVER_PATH
import os
from flask_cors import CORS, cross_origin


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
    return engine.ComicCrawler.start(**request.json)


@bp.route('/api/get_crawler_progress', methods=['POST'])
def get_progress():
    print(request.json)
    if 'crawler_id' in request.json:
        return engine.ComicCrawler.get_current_progress(request.json['crawler_id'])
    else:
        return json.dumps({
            "msg": "params error"
        })


@bp.route('/api/content', methods=['POST', 'OPTIONS'])
def get_book_content():
    if request.method == 'OPTIONS':
        return Response.headers
    data = request.json
    content, mimetype = engine.BookContent.process(**data)
    if mimetype.startswith('path'):
        name = mimetype.split('/')[-1]
        return send_file(content, attachment_filename=name)
    else:
        return Response(content, mimetype=mimetype)


@bp.route('/api/info', methods=['POST'])
def get_book_info():
    # if request.method == 'METHODS':
    #     response = Response()
    #     response.headers['Access-Control-Allow-Origin'] = '*'
    #     response.headers[
    #         'Access-Control-Allow-Headers'] = 'Access-Control-Allow-Headers, Origin, X-Requested-With, Content-Type, Accept, Authorization'
    #     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, HEAD'
    #     response.headers['Access-Control-Expose-Headers'] = '*'
    #     return response
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
    print(os.path.join(COVER_PATH, cover_name))
    file_path = os.path.abspath(os.path.join(COVER_PATH, cover_name))
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        raise FileNotFoundError


@bp.route('/api/list', methods=['POST'])
def get_list_query():
    params = request.json
    if 'query' not in params:
        return json.dumps({'msg': 'invalid query'})
    if params['query'] == 'time':
        if 'page' not in params:
            return json.dumps({'msg': 'invalid page number'})
        books = db.BookListQuery.get_books_by_time(page=int(params['page']))
        book_list = []
        while len(book_list) < 30:  # delete it after test !!!
            for book in books:
                book_info = {
                    'book_id': book.book_id,
                    'cover': book.cover,
                    'authors': [author.name for author in book.authors]
                }
                book_list.append(book_info)
        return json.dumps(book_list)
