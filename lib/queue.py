import os
from mrq import context, config
from mrq.job import queue_job

cfg = config.get_config(file_path="/mrq-config.py")
context.set_current_config(cfg)
