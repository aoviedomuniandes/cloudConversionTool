import threading
import atexit
from flask import Flask
from extensions import register_extensions
from config import config
import logging
from tasks import process_task
from google.cloud import pubsub_v1
import os
from concurrent import futures
from concurrent.futures import TimeoutError

POOL_TIME = 5 #Seconds

# variables that are accessible from anywhere
commonDataStruct = {}
# lock to control access to variable
dataLock = threading.Lock()
# thread handler
yourThread = threading.Thread()

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)

    def callback(message):
        logging.info(f"Received: {str(message.data)} | Current_threading = {str(threading.current_thread())}")
        dict_str = message.data.decode("UTF-8")
        process_task(dict_str,app)
        message.ack()

    def start_subscriber():
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'miso-grupo-2.json'
        project_id = "miso-grupo-2"
        subscription_id = "tasks-sub"
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_id)
        flow_control = pubsub_v1.types.FlowControl(max_messages=1)

        with pubsub_v1.SubscriberClient() as subscriber:
            streaming_pull_future = subscriber.subscribe(subscription_path, callback = callback ,flow_control=flow_control)
            timeout = 5 * 60  # seconds
            try:
                print("Buscando por nuevas tareas sin procesar...")
                streaming_pull_future.result(timeout=timeout)
            except TimeoutError:
                streaming_pull_future.cancel()  # Trigger the shutdown.
                streaming_pull_future.result()  # Block until the shutdown is complete.

    def interrupt():
        global yourThread
        yourThread.cancel()

    def doStuff():
        global commonDataStruct
        global yourThread
        with dataLock:
            start_subscriber()
            
        # Set the next thread to happen
        yourThread = threading.Timer(POOL_TIME, doStuff, ())
        yourThread.start()   

    def doStuffStart():
        # Do initialisation stuff here
        global yourThread
        # Create your thread
        yourThread = threading.Timer(POOL_TIME, doStuff, ())
        yourThread.start()

    

    # Initiate
    doStuffStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app

app = create_app()     