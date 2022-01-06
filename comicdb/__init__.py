__package__ = "comicdb"


import os
import sys

current_path = os.path.abspath(os.path.dirname(__file__))
print(current_path)
sys.path.append(current_path)


from services.db import create_all_db
from flask import Flask, request, Response, send_file
from services import logger
from services.engine import get_book_by_id
log = logger.create_logger('main')


class Platform:
    def __init__(self):
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        for folder_name in os.listdir(os.path.join(current_path, 'plugins')):
            if not folder_name.startswith('.'):
                self.run_plugin(module_name=folder_name)

    def run_plugin(self, module_name: str):
        plugin = __import__(f"plugins.{module_name}", fromlist=["__init__"])
        log.info(f"module [{module_name}] import successfully")
        self.plugins.append(plugin)


def create_app():
    create_all_db()
    app = Flask(__name__, instance_relative_config=True)
    app.config['CORS_HEADERS'] = 'Content-Type'
    import auth, bookinfo, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(bookinfo.bp)
    app.register_blueprint(api.bp)
    app.jinja_env.variable_start_string = '{['
    app.jinja_env.variable_end_string = ']}'
    platform = Platform()
    return app

