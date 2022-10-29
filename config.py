from datetime import timedelta
import os

BASEDIR = os.path.abspath(os.path.dirname(__name__))
SQLITE_DB = SQLITE_DB = "sqlite:///" + os.path.join(BASEDIR, "audioconverter.db")


class Config(object):
    DEBUG = False
    timezone = os.getenv("TIMEZONE", "America/Bogota")
    SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(16).hex())
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.urandom(16).hex())
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=50)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=20)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", SQLITE_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Celery new parameters
    BROKER_URL = os.getenv("BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("RESULT_BACKEND", "redis://localhost:6379/0")
    broker_url = os.getenv("BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.getenv("RESULT_BACKEND", "redis://localhost:6379/0")
    task_send_sent_event = True
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    enable_utc = True


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


# return active config
available_configs = dict(development=DevelopmentConfig, production=ProductionConfig)
selected_config = os.getenv("FLASK_ENV", "production")
config = available_configs.get(selected_config, "production")
