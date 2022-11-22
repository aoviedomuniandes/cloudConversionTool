import codecs
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

from flask_mail import Message

from extensions import mail
from helper.gcloud import GCloudClient
from modelos import db, Task, TaskStatus, User

SUBJECT = "ConversionTool: Notificación de finalización de conversión de archivo de audio"
BASE_DIR = Path(__file__).resolve().parent.parent
audio_formats = {
    "mp3": '{} "{}" -q:a 0 -map_metadata 0 -id3v2_version 3 "{}"',
    "wav": '{} "{}" -c:a pcm_s16le -f wav "{}"',
    "aac": '{} "{}" -c:a aac -strict experimental "{}"',
    "ogg": '{} "{}" -c:a libvorbis "{}"',
    "wma": '{} "{}" -c:a wmav2 "{}"',
}


def send_email(task):
    user = User.query.filter(User.id == task.user).first()
    template = os.path.join(BASE_DIR,"helper", "template.html")
    file = codecs.open(template, "r", 'utf-8')
    message = file.read()
    message = message.replace("{user}", user.username).replace("{file}", task.fileNameResult)
    msg = Message(SUBJECT, recipients=[user.email])
    msg.html = message
    mail.send(msg)


def process_task(json_data,app):
    data = json.loads(json_data)
    with app.app_context():
        new_task = Task.query.filter(Task.id == data.get("idTask")).first()

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

            resource_name = google_client.upload_from_filename_to_bucket(blob_name=target_file_path, path_to_file=new)
            new_task.fileNameResult = resource_name
            new_task.status = TaskStatus.PROCESSED
            db.session.commit()

            if os.path.exists(old_file):
                os.remove(old_file)
            if os.path.exists(new):
                os.remove(new)

            if os.getenv("FLASK_ENV", "") != "production":
                send_email(new_task)
