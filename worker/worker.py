import os
import gevent

from mrq.scheduler import _hash_task
from mrq.worker import Worker
from mrq.task import Task
from raven import Client


class BotWorker(Worker):

    def greenlet_scheduler(self):

        from mrq.scheduler import Scheduler
        scheduler = Scheduler(self.mongodb_jobs.mrq_scheduled_jobs)

        from mrq.context import connections
        tasks = list(connections.mongodb_jobs.mrq_scheduled_jobs.find())
        task_hashes = [x.get('hash') for x in tasks]

        for task in (self.config.get("scheduler_tasks") or []):
            if _hash_task(task) not in task_hashes:
                tasks.append(task)

        scheduler.sync_tasks(tasks)

        while True:
            scheduler.refresh()
            scheduler.check()
            gevent.sleep(int(self.config["scheduler_interval"]))


class BaseTask(Task):
    def __init__(self):
        super()
        RAVEN_DSN = os.environ.get('SENTRY_URL')
        self.raven = Client(RAVEN_DSN) if RAVEN_DSN is not None else Client()

    def run_wrapped(self, params):
        try:
            return self.run(params)
        except Exception as e:
            self.raven.captureException()
            raise e
