__package__ = "comicdb"


import os
import sys

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)

from flask import Flask, render_template
from services import logger, pre_start

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
    pre_start.start()
    app = Flask(__name__,
                static_url_path='',
                static_folder='./static',
                template_folder="./templates"
                )
    app.config['CORS_HEADERS'] = 'Content-Type'
    import auth, bookinfo, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(bookinfo.bp)
    app.register_blueprint(api.bp)
    app.jinja_env.variable_start_string = '{['
    app.jinja_env.variable_end_string = ']}'

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/<path>')
    def fallback(path):
        if path.startswith('css/') or path.startswith('js/') \
                or path.startswith('img/') or path == 'favicon.ico':
            return app.send_static_file(path)
        else:
            return render_template('index.html')

    @app.route('/book/<path>')
    def jump_to(path):
        return render_template('index.html')

    @app.route('/read/<path>')
    def _jump_to(path):
        return render_template('index.html')

    platform = Platform()
    return app

