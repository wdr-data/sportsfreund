import gevent
from mrq.scheduler import _hash_task
from mrq.worker import Worker


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
