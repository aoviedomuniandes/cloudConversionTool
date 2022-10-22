from celery import Celery
from flask import Flask
from modelos import db
from flask_jwt_extended import JWTManager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'frase-secreta'
app.config['PROPAGATE_EXCEPTIONS'] = True
UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app_context = app.app_context()
app_context.push()
db.init_app(app)
db.create_all()

jwt = JWTManager(app)

if __name__ == '__main__':
    app.run()

from vistas import *  # noqa: F401,F403