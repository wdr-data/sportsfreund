from lib.mongodb import db
from .model import Model
from enum import Enum

class Subscription(Model):

    collection = db.subscriptions

    class Target(Enum):
        SPORT = 'sport'
        DISCIPLINE = 'discipline'
        ATHLETE = 'athlete'

    class Type(Enum):
        RESULT = 'result'

    @classmethod
    def create(cls, psid, target, filter, type):

        if target not in cls.Target:
            raise ValueError(f'invalid target: {target}')

        if type not in cls.Type:
            raise ValueError(f'invalid type: {type}')

        if not isinstance(filter,dict):
            raise ValueError(f'filter should be dict: {filter}')

        data = {
            psid: psid,
            target: target,
            filter: filter,
            type: type,
        }

        cls.collection.replace_one(data, data, upsert=True)

