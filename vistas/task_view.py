import subprocess
import http
import os
import time
from uuid import uuid4
from extensions import celery
from flask import request
from modelos import User, db, Task, TaskSchema, TaskStatus
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
from pathlib import Path

task_view = Blueprint("task_view", __name__, url_prefix="/api")
task_schema = TaskSchema()

ALLOWED_EXTENSIONS = {'mp3', 'acc', 'ogg', 'wav', 'wma'}
BASEDIR = os.path.abspath(os.path.dirname(__name__))
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR.joinpath("files")


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

        if file and new_format and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            final_name = f"{uuid4()}_{filename}"
            file.save(os.path.join(BASEDIR + "/files", final_name))
            new_task = Task(fileName=final_name, newFormat=new_format, user=user_info.id)
            db.session.add(new_task)
            db.session.commit()
            task_celery = add_task.apply_async(args=[new_task.id], link_error=error_handler.s())
            new_task.idTask = task_celery.id
            db.session.add(new_task)
            db.session.commit()
            return task_schema.dump(new_task)
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@celery.task(bind=True)
def add_task(self, id_task):
    new_task = Task.query.filter(Task.id == id_task).first()
    audio_formats = {
        "mp3": '{} "{}" -q:a 0 -map_metadata 0 -id3v2_version 3 "{}"',
        "wav": '{} "{}" -c:a pcm_s16le -f wav "{}"',
        "aac": '{} "{}" -c:a aac -strict experimental "{}"',
        "ogg": '{} "{}" -c:a libvorbis "{}"',
        "wma": '{} "{}" -c:a wmav2 "{}"',
    }
    file_name, file_extension = os.path.splitext(new_task.fileName)
    new_format = f".{new_task.newFormat.name.lower()}"
    target_file_path = new_task.fileName.replace(file_extension, new_format)

    if new_task.newFormat.name.lower() in audio_formats:
        start = time.perf_counter()
        old = os.path.join(UPLOAD_FOLDER, new_task.fileName)
        new = os.path.join(UPLOAD_FOLDER, target_file_path)
        exec_process = audio_formats[new_task.newFormat.name.lower()].format("ffmpeg -i", old, new)
        print(exec_process)
        subprocess.run(exec_process)
        end = time.perf_counter()
        total_time = end - start
        print(f"Duracion de la tarea: {total_time} ")
        # update task
        new_task.status = TaskStatus.PROCESSED
        db.session.commit()
    self.update_state(
        state="PROGRESS", meta={"fileold": new_task.fileName, "filenew": target_file_path}
    )
    return {"status": "PROCESSED", "fileold": new_task.fileName, "filenew": target_file_path}


@celery.task
def error_handler(request, exc, traceback):
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
        request.id, exc, traceback))


@task_view.route("/tasks/<int:id_task>", methods=["GET"])
@jwt_required()
def get(id_task):
    task = Task.query.filter(Task.id == id_task).first()
    user = User.query.filter(User.id == task.user).first()
    if task is not None:
        task = AsyncResult(task.idTask)
        if task.state == "PENDING":
            # job did not start yet
            response = {"state": task.state,
                        "status": "Pending process...",
                        "user": user.username,
                        "file_old": task.info.get("fileold", ""),
                        "file_new": task.info.get("filenew", ""),
                        }

        elif task.state != "FAILURE":
            response = {
                "state": task.state,
                "status": task.info.get("status", ""),
                "user": user.username,
                "file_old": task.info.get("fileold", ""),
                "file_new": task.info.get("filenew", ""),
            }

        else:
            # something went wrong in the background job
            response = {
                "state": task.state,
                "status": str(task.info)
            }
        return jsonify(response)
    else:
        return {"mensaje": "el id_task no existe!"}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value
