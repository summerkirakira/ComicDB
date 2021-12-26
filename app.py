from flask import Flask
import datetime
from services.db import create_all_db, add_new_book, get_author_by_id, update_book_info
from services import engine
import os
from flask import Flask, request, Response
from services import logger


log = logger.create_logger('app')


class Platform:
    def __init__(self):
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        for folder_name in os.listdir("plugins"):
            self.run_plugin(module_name=folder_name)

    def run_plugin(self, module_name: str):
        plugin = __import__(f"plugins.{module_name}", fromlist=["__init__"])
        log.info(f"module [{module_name}] import successfully")
        self.plugins.append(plugin)


create_all_db()
platform = Platform()
log.debug('Platform start successful')

app = Flask(__name__)


@app.route('/api/content', methods=['GET'])
def get_book_content():
    data = request.args
    content, mimetype = engine.BookContent.process(**data)
    return Response(content, mimetype=mimetype)


if __name__ == '__main__':
    app.run()
