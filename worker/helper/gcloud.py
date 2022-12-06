import os
from pathlib import Path
import json
from google.cloud import pubsub_v1
import google.cloud.storage as storage


class GCloudClient:
    BASE_DIR = Path('/tmp').resolve()
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']='miso-grupo-2.json'
    _DEFAULT_BUCKET = "cloudconversiontools-bucket"
    _project_id = "miso-grupo-2"
    _topic_id = "tasks"

    def upload_from_file_to_bucket(self, blob_name, path_to_file, bucket_name: str = _DEFAULT_BUCKET):
        storage_client = storage.Client.from_service_account_json('miso-grupo-2.json')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_file(path_to_file)
        return blob.name

    def upload_from_filename_to_bucket(self, blob_name, path_to_file, bucket_name: str = _DEFAULT_BUCKET):
        storage_client = storage.Client.from_service_account_json('miso-grupo-2.json')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(path_to_file)
        return blob.name

    def download_file_to_bucket(self, resource_name, bucket_name: str = _DEFAULT_BUCKET):
        storage_client = storage.Client.from_service_account_json('miso-grupo-2.json')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(resource_name)
        str_path = "{}/{}".format(self.BASE_DIR, resource_name)
        blob.download_to_filename(str_path)
        return Path(str_path)

    def delete_file_to_bucket(self,resource_name, bucket_name: str = _DEFAULT_BUCKET):
        storage_client = storage.Client.from_service_account_json('miso-grupo-2.json')
        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(resource_name)
        blob.delete()

    def send_task(self,task_id,file,new_format):
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(self._project_id, self._topic_id)

        data_dict = {
            "idTask":task_id,
            "file":file,
            "newFormat":new_format
        }

        data_str = json.dumps(data_dict)
        # Data must be a bytestring
        data = data_str.encode("utf-8")
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data)
        print(future.result())        