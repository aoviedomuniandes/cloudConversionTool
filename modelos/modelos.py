from flask_sqlalchemy import SQLAlchemy
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.sql import expression
import enum
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from marshmallow import fields

db = SQLAlchemy()


class TaskStatus(enum.Enum):
    UPLOADED = 1
    PROCESSED = 2


class Formats(enum.Enum):
    MP3 = 1
    WAV = 2
    OGG = 3
    WMA = 4
    AAC = 5


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(100), index=True, unique=True)
    password = db.Column(db.String(512))
    status = db.Column(db.Boolean, server_default=expression.true())
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey("user.id"))
    idTask = db.Column(db.String(128))
    fileName = db.Column(db.String(512))
    fileNameResult = db.Column(db.String(512))
    newFormat = db.Column(db.Enum(Formats))
    timeStamp = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.UPLOADED)


class EnumToDictionary(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return {"name": value.name, "value": value.value}


class TaskSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        include_relationships = True
        load_instance = True

    newFormat = EnumToDictionary(attribute=("newFormat"))
    status = EnumToDictionary(attribute=("status"))


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_relationships = True
        load_instance = True

    tasks = fields.List(fields.Nested(TaskSchema()))
