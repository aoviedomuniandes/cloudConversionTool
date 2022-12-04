from flask import Flask
from extensions import register_extensions
from vistas import register_blueprints
from config import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.url_map.strict_slashes = False

    register_extensions(app)
    register_blueprints(app)

    return app
