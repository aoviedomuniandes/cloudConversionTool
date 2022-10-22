from celery import Celery
import subprocess
import time
from modelos import TaskStatus, db, Task
import os
from pathlib import Path
from celery.signals import task_postrun

celery_app = Celery(__name__, broker='redis://localhost:6379/0')
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_FOLDER = BASE_DIR.joinpath("files")


@celery_app.task(name='process_task')
def process_task(json):
    print(f"procesando tarea ({json})")
    new_task = Task.query.get_or_404(json['taskid'])
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
        subprocess.run(exec_process)
        end = time.perf_counter()
        total_time = end - start
        print(f"Duracion de la tarea: {total_time} ")

        # update task
        new_task.status = TaskStatus.PROCESSED
        db.session.commit()

        # send email


@task_postrun.connect()
def close_session(*args, **kwargs):
    db.session.remove()
