from celery import Celery
from flask import Flask
from extensions import register_extensions
from modelos import db
from flask_jwt_extended import JWTManager
from vistas import register_blueprints
from config import config

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    app.url_map.strict_slashes = False


if __name__ == '__main__':
    app.run()




    return app
