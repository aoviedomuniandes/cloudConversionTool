from flask import Flask

from .task_view import task_view
from .user_view import user_view


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(task_view)
    app.register_blueprint(user_view)

