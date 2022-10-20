import http
import os
from uuid import uuid4
from flask import request
from werkzeug.utils import secure_filename
from flask import jsonify
import json

from app import app
from modelos import User, db, Task, TaskSchema
from flask_jwt_extended import create_access_token, jwt_required
from flask_jwt_extended.utils import get_jwt_identity

ALLOWED_EXTENSIONS = {'mp3', 'acc', 'ogg', 'wav', 'wma'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def add_task():
    try:
        user_id = get_jwt_identity()
        user_info = User.query.get_or_404(user_id)

        file = request.files["fileName"]
        new_format = str(request.form.get("newFormat")).upper()

        if file and new_format and allowed_file(file.filename):
            #guardamos el archivo
            filename = secure_filename(file.filename)
            final_name = f"{uuid4()}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], final_name))
            #guardamos la terea
            new_task = Task(fileName=final_name, newFormat=new_format, user=user_info.id)
            db.session.add(new_task)
            db.session.commit()
            #TODO: enviamos a la cola
            task_schema = TaskSchema()
            return task_schema.dump(new_task)

        else:
            return {"mensaje": "Los datos no son validos."}, http.HTTPStatus.BAD_REQUEST.value

    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value

@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        user_id = get_jwt_identity()
        task_schema = TaskSchema()
        tasks = [json.loads(task_schema.dumps(task)) for task in Task.query.filter(Task.user == user_id)]
        return jsonify(tasks)

    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value

