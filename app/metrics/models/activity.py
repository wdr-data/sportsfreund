from prometheus_client import Gauge

from lib.model import Model
from lib.mongodb import db


class UserActivity(Model):
    collection = db.metrics_activity

    @classmethod
    def capture(cls, type, payload):
        filter = {'type': type, 'payload': payload}
        cls.collection.update_one(filter, {'$set': filter, '$inc': {'count': 1}}, upsert=True)


g = Gauge('user_activity', "Activity on different intents", ['type', 'payload'])


def collect():
    activities = UserActivity.collection.find()
    for activity in activities:
        g.labels(activity['type'], activity['payload']).set(activity['count'])
