import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
# Ugly hack: Django somehow guesses the timezone and that changes global datetime behaviour. This resets that
del os.environ['TZ']
time.tzset()

MONGODB_JOBS = os.environ.get('MONGODB_URI')
REDIS = os.environ.get('REDIS_URL')

GREENLETS = 5
# Check if running on Heroku
HEROKU_RAM = os.environ.get('DYNO_RAM')
if HEROKU_RAM is not None:
    GREENLETS = int(HEROKU_RAM) / 512 * 15

WORKER_CLASS = "worker.BotWorker"
SCHEDULER = True
SCHEDULER_INTERVAL = 30
SCHEDULER_TASKS = [
    {
        'path': 'push.UpdateSchedule',
        'params': {},
        'interval': 60 * 15
    },
    {
        'path': 'push.SendMedals',
        'params': {},
        'interval': 60 * 5,
    },

    # MRQ maintenance jobs

    # This will requeue jobs in the 'retry' status, until they reach their max_retries.
    {
        "path": "mrq.basetasks.cleaning.RequeueRetryJobs",
        "params": {},
        "interval": 60
    },

    # This will requeue jobs marked as interrupted, for instance when a worker received SIGTERM
    {
        "path": "mrq.basetasks.cleaning.RequeueInterruptedJobs",
        "params": {},
        "interval": 5 * 60
    },

    # This will requeue jobs marked as started for a long time (more than their own timeout)
    # They can exist if a worker was killed with SIGKILL and not given any time to mark
    # its current jobs as interrupted.
    {
        "path": "mrq.basetasks.cleaning.RequeueStartedJobs",
        "params": {},
        "interval": 3600
    },

    # This will requeue jobs 'lost' between redis.blpop() and mongo.update(status=started).
    # This can happen only when the worker is killed brutally in the middle of dequeue_jobs()
    {
        "path": "mrq.basetasks.cleaning.RequeueLostJobs",
        "params": {},
        "interval": 24 * 3600
    },
]
