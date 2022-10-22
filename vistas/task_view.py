
from datetime import datetime
from datetime import timedelta
import http
import os
import time
from uuid import uuid4
from extensions import celery
from flask import request
from modelos import User, db, Task, TaskSchema
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from werkzeug.utils import secure_filename
from celery.result import AsyncResult


task_view = Blueprint("task_view", __name__,  url_prefix="/api")
task_schema = TaskSchema()

ALLOWED_EXTENSIONS = {'mp3', 'acc', 'ogg', 'wav', 'wma'}

BASEDIR = os.path.abspath(os.path.dirname(__name__))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@task_view.route('/tasks', methods=['POST'])
@jwt_required()
def file_converter():
    try:
        user_id = get_jwt_identity()
        user_info = User.query.get_or_404(user_id)

        file = request.files["fileName"]
        new_format = str(request.form.get("newFormat")).upper()

        eta = datetime.utcnow() + timedelta(seconds=10)

        if file and new_format and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                final_name = f"{uuid4()}_{filename}"
                file.save(os.path.join(BASEDIR + '/Uploads', final_name))
                new_task = Task(fileName=final_name, newFormat=new_format, user=user_info.id)
                task = add_task.apply_async((new_task.user, new_task.fileName), eta=eta, link_error=error_handler.s())

                new_task.idTask = task.id
                db.session.add(new_task)
                db.session.commit()
                return (
                    jsonify(
                        {"id_task": new_task.id, "mesagge": "Tarea creada correctamente"}
                    ),
                    202,
                 )
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@celery.task(bind=True)
def add_task(self, user, filename):
    self.update_state(
            state="PROGRESS", meta={"User": user , "file": filename, "status": "created"}
    )
    time.sleep(1)
    return {"status": "PROCESSED"}



@celery.task
def error_handler(request, exc, traceback):
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          request.id, exc, traceback))


@task_view.route("/tasks/<int:id_task>", methods=["GET"])
@jwt_required()
def get(id_task):
    task = Task.query.filter(Task.id == id_task).first()
    task = AsyncResult(task.idTask)
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state, "status": "Pending..."}

    elif task.state != "FAILURE":
        response = {
            "state": task.state,
            "status": task.info.get("status", ""),
        }
        if "result" in task.info:
            response["result"] = task.info["result"]
    else:
        # something went wrong in the background job
        response = {
            "state": task.state,
            "status": str(task.info),  # this is the exception raised
        }
    return jsonify(response)




