from modelos import db
from flask_mail import Mail
from healthcheck import HealthCheck

mail = Mail()
health = HealthCheck()


def register_extensions(app):
    app_context = app.app_context()
    app_context.push()

    mail.init_app(app)
    db.init_app(app)
    db.create_all()

    # Add a flask route to expose information
    app.add_url_rule("/", "", view_func=health.run)
