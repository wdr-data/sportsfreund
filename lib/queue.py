import datetime
import os
from mrq import context, config
from mrq.job import queue_job
from mrq.scheduler import _hash_task

config_locations = ["../worker/mrq-config.py", "./worker/mrq-config.py", "/mrq-config.py"]
file_path = None

for path in config_locations:
    if os.path.isfile(path):
        file_path = path

if file_path is None:
    raise RuntimeError("MRQ Config not found!")

cfg = config.get_config(file_path=file_path)
context.set_current_config(cfg)


def _assemble_task_data(main_task_path, params, interval, queue=None):
    task_data = {}

    if main_task_path is not None:
        task_data['path'] = main_task_path

    if params is not None:
        task_data['params'] = params

    if interval is not None:
        task_data['interval'] = interval

    if queue is not None:
        task_data['queue'] = queue

    return task_data


def add_scheduled(main_task_path, params, interval, queue=None):
    task_data = _assemble_task_data(main_task_path, params, interval, queue)
    task_data["datelastqueued"] = datetime.datetime.fromtimestamp(0)
    task_data['hash'] = _hash_task(task_data)
    context.connections.mongodb_jobs.mrq_scheduled_jobs.update_one(
        {'hash': task_data['hash']},
        {"$set": task_data},
        upsert=True
    )


def get_scheduled(main_task_path=None, params=None, interval=None, queue=None):
    query = _assemble_task_data(main_task_path, params, interval, queue)
    return context.connections.mongodb_jobs.mrq_scheduled_jobs.find(query)


def remove_scheduled(main_task_path, params, interval, queue=None):
    hash = _hash_task(_assemble_task_data(main_task_path, params, interval, queue))
    context.connections.mongodb_jobs.mrq_scheduled_jobs.delete_one({'hash': hash})
