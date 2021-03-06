from datetime import datetime
import os
from mrq import context, config
import mrq.job
from mrq.scheduler import _hash_task


def configure_maybe():
    if not context.get_current_config():
        config_locations = ["../worker/mrq-config.py", "./worker/mrq-config.py", "/mrq-config.py"]
        file_path = None

        for path in config_locations:
            if os.path.isfile(path):
                file_path = path

        if file_path is None:
            raise RuntimeError("MRQ Config not found!")

        cfg = config.get_config(file_path=file_path)
        context.set_current_config(cfg)


def queue_job(*args, **kwargs):
    configure_maybe()
    mrq.job.queue_job(*args, **kwargs)


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


def add_scheduled(main_task_path, params, interval, start_at=None, queue=None):
    configure_maybe()
    task_data = _assemble_task_data(main_task_path, params, interval, queue)
    task_data['hash'] = _hash_task(task_data)

    if isinstance(start_at, datetime):
        task_data["datelastqueued"] = start_at
    else:
        task_data["datelastqueued"] = datetime.fromtimestamp(0)

    context.connections.mongodb_jobs.mrq_scheduled_jobs.update_one(
        {'hash': task_data['hash']},
        {"$set": task_data},
        upsert=True
    )


def get_scheduled(main_task_path=None, params=None, interval=None, queue=None):
    configure_maybe()
    query = _assemble_task_data(main_task_path, params, interval, queue)
    return context.connections.mongodb_jobs.mrq_scheduled_jobs.find(query)


def remove_scheduled(main_task_path, params, interval, queue=None):
    configure_maybe()
    hash = _hash_task(_assemble_task_data(main_task_path, params, interval, queue))
    context.connections.mongodb_jobs.mrq_scheduled_jobs.delete_one({'hash': hash})
