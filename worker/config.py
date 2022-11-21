from datetime import timedelta
import os


class Config(object):
    DEBUG = False
    timezone = os.getenv("TIMEZONE", "America/Bogota")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=50)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(minutes=20)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # mail_server
    MAIL_ACTIVE_SEND = os.getenv("MAIL_ACTIVE_SEND", True)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "misocloudconversiontool@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "qiprmooobpxvbuea")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", " misocloudconversiontool@gmail.com")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    pass


# return active config
available_configs = dict(development=DevelopmentConfig, production=ProductionConfig)
selected_config = os.getenv("FLASK_ENV", "production")
config = available_configs.get(selected_config, "production")
