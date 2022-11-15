import subprocess
import http
import os
import time
from uuid import uuid4
from extensions import celery
from flask import request
from helper.mail_helper import send_async_email
from modelos import User, db, Task, TaskSchema, TaskStatus
from flask import Blueprint, jsonify, send_from_directory, send_file
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
from pathlib import Path
import mimetypes
from helper.gcloud import GCloudClient
import tempfile

task_view = Blueprint("task_view", __name__, url_prefix="/api")
task_schema = TaskSchema()

ALLOWED_EXTENSIONS = {'mp3', 'aac', 'ogg', 'wav', 'wma'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_task(task, user, idTask):
    if task.state == "PENDING":
        # job did not start yet
        response = {"state": task.state,
                    "status": "Pending process...",
                    "user": user.username,
                    "file_old": task.info.get("fileold", ""),
                    "file_new": task.info.get("filenew", ""),
                    "id": idTask
                    }

    elif task.state != "FAILURE":
        response = {
            "state": task.state,
            "status": task.info.get("status", ""),
            "user": user.username,
            "file_old": task.info.get("fileold", ""),
            "file_new": task.info.get("filenew", ""),
            "id": idTask
        }

    else:
        # something went wrong in the background job
        response = {
            "state": task.state,
            "status": str(task.info),
            "id": idTask
        }

    return response


@task_view.route('/tasks', methods=['POST'])
@jwt_required()
def file_converter():
    try:
        user_id = get_jwt_identity()
        user_info = User.query.get_or_404(user_id)

        file_request = request.files["fileName"]
        new_format = str(request.form.get("newFormat")).upper()

        if file_request and new_format and allowed_file(file_request.filename):
            filename = secure_filename(file_request.filename)
            final_name = f"{uuid4()}_{filename}"
            google_client = GCloudClient()
            bucket_path = google_client.upload_from_file_to_bucket(blob_name=final_name, path_to_file=file_request)
            new_task = Task(fileName=bucket_path, newFormat=new_format, user=user_info.id)
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

    google_client = GCloudClient()
    old_file = google_client.download_file_to_bucket(resource_name=new_task.fileName)
    file_name, file_extension = os.path.splitext(old_file)
    new_format = f".{new_task.newFormat.name.lower()}"
    target_file_path = new_task.fileName.replace(file_extension, new_format)

    if new_task.newFormat.name.lower() in audio_formats:
        start = time.perf_counter()
        new = os.path.join(tempfile.gettempdir(), target_file_path)
        exec_process = audio_formats[new_task.newFormat.name.lower()].format("ffmpeg -i", old_file, new)
        print(exec_process)
        subprocess.call(exec_process, shell=True)
        end = time.perf_counter()
        total_time = end - start
        print(f"Duracion de la tarea: {total_time} ")
        resource_name = google_client.upload_from_filename_to_bucket(blob_name=target_file_path,path_to_file=new)
        new_task.fileNameResult = resource_name
        new_task.status = TaskStatus.PROCESSED
        db.session.commit()

        if os.path.exists(old_file):
            os.remove(old_file)
        if os.path.exists(new):
            os.remove(new)     

        if os.getenv("FLASK_ENV","") != "production":
            send_async_email.apply_async(args=[new_task.id], link_error=error_handler.s())
    self.update_state(
        state="PROGRESS", meta={"fileold": new_task.fileName, "filenew": target_file_path}
    )
    return {"status": "PROCESSED", "fileold": new_task.fileName, "filenew": target_file_path}


@celery.task
def error_handler(request, exc, traceback):
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
        request.id, exc, traceback))


@task_view.route('/tasks/<int:id_task>', methods=['GET'])
@jwt_required()
def get(id_task):
    task = Task.query.filter(Task.id == id_task).first()
    user = User.query.filter(User.id == task.user).first()
    if task is not None:
        task = AsyncResult(task.idTask)
        response = format_task(task, user, task.id)
        return jsonify(response)
    else:
        return {"mensaje": "el id_task no existe!"}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@task_view.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    args = request.args

    # Handle optional query params
    try:
        max = args.getlist("max")[0]
    except IndexError:
        max = 0
    try:
        order = args.getlist("order")[0]
    except IndexError:
        order = 0

    user_id = get_jwt_identity()
    user = User.query.filter(User.id == user_id).first()
    tasks = []

    # Limit and sort the query results
    if (int(max) > 0):
        tasks = Task.query.filter(Task.user == user_id).order_by(
            Task.id.desc() if int(order) == 1 else Task.id.asc()).limit(str(max))
    else:
        tasks = Task.query.filter(Task.user == user_id).order_by(Task.id.desc() if int(order) == 1 else Task.id.asc())

    responseList = []

    for task in tasks:
        idTask = task.id
        task = AsyncResult(task.idTask)
        response = format_task(task, user, idTask)
        responseList.append(response)

    return jsonify(responseList)


@task_view.route('/tasks/<int:id_task>', methods=['DELETE'])
@jwt_required()
def delete(id_task):
    task = Task.query.filter(Task.id == id_task).first()
    if not task:
        return '', http.HTTPStatus.NOT_FOUND.value

    google_client = GCloudClient()

    if task.status == TaskStatus.PROCESSED:
        if task.fileName is not None:
            google_client.delete_file_to_bucket(task.fileName)

        if task.fileNameResult is not None:
            google_client.delete_file_to_bucket(task.fileNameResult)
            
    db.session.delete(task)
    db.session.commit()

    return '', http.HTTPStatus.NO_CONTENT.value


@task_view.route('/files/<filename>', methods=['GET'])
@jwt_required()
def download_task(filename):
    task_query = Task.query.filter(Task.fileName == filename).first()
    google_client = GCloudClient()
    if task_query is None:
        return '', http.HTTPStatus.NOT_FOUND.value

    if task_query.status == TaskStatus.UPLOADED:
        file_name = task_query.fileName
    else:
        file_name = task_query.fileNameResult

    temporal_path = google_client.download_file_to_bucket(resource_name=file_name)
    source_file = temporal_path.resolve()    
    mimetype = mimetypes.MimeTypes().guess_type(source_file)[0]
    return send_file(open(str(source_file), "rb"), mimetype=mimetype, attachment_filename=source_file)


@task_view.route('/tasks/<int:id_task>', methods=['PUT'])
@jwt_required()
def put(id_task):
    update_task = Task.query.filter(Task.id == id_task).first()
    new_format = str(request.form.get("newFormat")).upper()

    if update_task is not None:

        google_client = GCloudClient()

        if update_task.fileNameResult is not None:
            google_client.delete_file_to_bucket(update_task.fileNameResult)

        update_task.newFormat = new_format
        update_task.status = TaskStatus.UPLOADED
        file_name, file_extension = os.path.splitext(update_task.fileName)
        dot_new_format = f".{new_format.lower()}"
        target_file_path = update_task.fileName.replace(file_extension, dot_new_format)
        update_task.fileNameResult = None
        db.session.commit()

        task_celery = add_task.apply_async(args=[update_task.id], link_error=error_handler.s())
        update_task.idTask = task_celery.id
        db.session.commit()

        return task_schema.dump(update_task)
    else:
        return {"mensaje": "el id_task no existe!"}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value



