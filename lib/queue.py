import os
from mrq import context, config
from mrq.job import queue_job

config_locations = ["../worker/mrq-config.py", "./worker/mrq-config.py", "/mrq-config.py"]
file_path = None

for path in config_locations:
    if os.path.isfile(path):
        file_path = path

if file_path is None:
    raise RuntimeError("MRQ Config not found!")

cfg = config.get_config(file_path=file_path)
context.set_current_config(cfg)
