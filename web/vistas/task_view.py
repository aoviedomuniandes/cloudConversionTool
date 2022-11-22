import http
import os
from uuid import uuid4
from flask import request
from modelos import User, db, Task, TaskSchema, TaskStatus
from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from werkzeug.utils import secure_filename
import mimetypes
from helper.gcloud import GCloudClient

task_view = Blueprint("task_view", __name__, url_prefix="/api")
task_schema = TaskSchema()

ALLOWED_EXTENSIONS = {'mp3', 'aac', 'ogg', 'wav', 'wma'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

            google_client.send_task(task_id=new_task.id,file=new_task.fileName,new_format=new_format)

            return task_schema.dump(new_task)
    except Exception as e:
        return {"mensaje": str(e)}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value


@task_view.route('/tasks/<int:id_task>', methods=['GET'])
@jwt_required()
def get(id_task):
    task = Task.query.filter(Task.id == id_task).first()
    if task is not None:
        return task_schema.dump(task)
    
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
        response =  task_schema.dump(task)
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
        update_task.fileNameResult = None
        db.session.commit()
        google_client.send_task(task_id=update_task.id,file=update_task.fileName,new_format=new_format)
        return task_schema.dump(update_task)
    else:
        return {"mensaje": "el id_task no existe!"}, http.HTTPStatus.INTERNAL_SERVER_ERROR.value



