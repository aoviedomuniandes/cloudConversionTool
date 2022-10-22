import http
from flask import request
from flask_inputs import Inputs
from flask import Blueprint
from celery import Celery

file_view = Blueprint("file_view", __name__, url_prefix="/api/files")

@file_view.route('/<filename>', methods=['GET'])
def retrieveOriginalFile():
    try:
            return {"mensaje": "usuario creado exitosamente."}
      
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


def convertFile(filename, newFormat):
    try:


        return {"mensaje": "usuario creado exitosamente."}
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value