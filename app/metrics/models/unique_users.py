from prometheus_client import Gauge

from lib.model import Model
from lib.mongodb import db


class UserListing(Model):
    collection = db.metrics_unique_user

    @classmethod
    def capture(cls, psid):
        return cls.collection.replace_one({'psid': psid}, {'psid': psid}, upsert=True)

    @classmethod
    def count(cls):
        return cls.collection.count()


g = Gauge('unique_users', 'Unique PSIDs used in interactions with the Bot')


def collect():
    g.set(UserListing.count())
