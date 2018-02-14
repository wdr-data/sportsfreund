import os
import redis as redis_


HANDLED_UPDATES_FB = 'handled_updates_fb'

try:
    REDIS_URL = os.environ['REDIS_URL']
    redis = redis_.StrictRedis.from_url(REDIS_URL)

except KeyError:
    redis = None
