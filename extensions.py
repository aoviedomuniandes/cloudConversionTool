from celery import Celery
from modelos import db
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from healthcheck import HealthCheck



celery = Celery()
jwt = JWTManager()
mail = Mail()
health = HealthCheck()



def register_extensions(app, worker=False):
    app_context = app.app_context()
    app_context.push()

    mail.init_app(app)
    db.init_app(app)
    db.create_all()

    jwt.init_app(app)

    # load celery config
    celery.config_from_object(app.config)

    # Add a flask route to expose information
    app.add_url_rule("/healthcheck", "healthcheck", view_func=health.run)

    if not worker:
        # register celery irrelevant extensions
        pass