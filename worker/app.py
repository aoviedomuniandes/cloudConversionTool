import logging
import os
import threading
from concurrent import futures
from concurrent.futures import TimeoutError
from threading import Thread

from flask import Flask
from google.cloud import pubsub_v1

from config import config
from extensions import register_extensions
from tasks import process_task


def callback(message):
    logging.info(f"Received: {str(message.data)} | Current_threading = {str(threading.current_thread())}")
    dict_str = message.data.decode("UTF-8")
    process_task(dict_str, create_app())
    message.ack()


def start_subscriber():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'miso-grupo-2.json'
    project_id = "miso-grupo-2"
    subscription_id = "tasks-sub"
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    executor = futures.ThreadPoolExecutor(max_workers=1)
    flow_control = pubsub_v1.types.FlowControl(max_messages=1)
    scheduler = pubsub_v1.subscriber.scheduler.ThreadScheduler(executor)

    with pubsub_v1.SubscriberClient() as subscriber:
        streaming_pull_future = subscriber.subscribe(subscription_path, callback, scheduler=scheduler,
                                                     await_callbacks_on_shutdown=True, flow_control=flow_control)

        timeout = 5 * 60  # seconds
        try:
            streaming_pull_future.result(timeout=timeout)
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    register_extensions(app)
    t = Thread(target=start_subscriber)
    t.start() 
    return app
