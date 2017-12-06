import os

MONGODB_JOBS = os.environ.get('MONGODB_URI')
REDIS = os.environ.get('REDIS_URL')

WORKER_CLASS = "worker.BotWorker"
SCHEDULER = True
SCHEDULER_INTERVAL = 30
SCHEDULER_TASKS = [
    {
        'path': 'push.UpdateSchedule',
        'params': {},
        'interval': 60 * 60
    }
]
