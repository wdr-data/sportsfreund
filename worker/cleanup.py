from time import time

from mrq.context import log
from worker import BaseTask

from lib.redis import redis, HANDLED_UPDATES_FB

FB_UPDATES_CACHE_TIME = 60 * 60


class HandledUpdates(BaseTask):

    def run(self, params):
        max_time = time() - FB_UPDATES_CACHE_TIME
        num = redis.zremrangebyscore(HANDLED_UPDATES_FB, '-inf', max_time)
        log.info(f'Deleted {num} already handled message IDs')
