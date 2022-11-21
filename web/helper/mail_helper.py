import codecs
import os
from flask_mail import Message
from extensions import celery, mail
from modelos import User, Task
from pathlib import Path

SUBJECT = "ConversionTool: Notificación de finalización de conversión de archivo de audio"
BASE_DIR = Path(__file__).resolve().parent

@celery.task
def send_async_email(id_task):
    """Background task to send an email with Flask-Mail."""
    task = Task.query.filter(Task.id == id_task).first()
    user = User.query.filter(User.id == task.user).first()
    template = os.path.join(BASE_DIR, "template.html")
    file = codecs.open(template , "r", 'utf-8')
    message = file.read()
    message = message.replace("{user}", user.username).replace("{file}",task.fileNameResult)
    #todo replace variable to data user
    msg = Message(SUBJECT,
                  recipients=[user.email])
    msg.html = message
    mail.send(msg)
 