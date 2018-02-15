import contextlib

import os
import redis as redis_


HANDLED_UPDATES_FB = 'handled_updates_fb'
REDIS_URL = os.environ.get('REDIS_URL')


@contextlib.contextmanager
def redis_connection():
    redis = redis_.StrictRedis.from_url(REDIS_URL)
    yield redis
    redis.connection_pool.disconnect()
