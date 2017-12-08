import os

MONGODB_JOBS = os.environ.get('MONGODB_URI')
REDIS = os.environ.get('REDIS_URL')

GREENLETS = 4

WORKER_CLASS = "worker.BotWorker"
SCHEDULER = True
SCHEDULER_INTERVAL = 30
SCHEDULER_TASKS = [
    {
        'path': 'push.UpdateSchedule',
        'params': {},
        'interval': 60 * 60
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
