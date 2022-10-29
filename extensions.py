from celery import Celery
from modelos import db
from flask_jwt_extended import JWTManager

celery = Celery()
jwt = JWTManager()

def register_extensions(app, worker=False):
    app_context = app.app_context()
    app_context.push()
    
    db.init_app(app)
    db.create_all()

    jwt.init_app(app)

    # load celery config
    celery.config_from_object(app.config)

    if not worker:
        # register celery irrelevant extensions
        pass