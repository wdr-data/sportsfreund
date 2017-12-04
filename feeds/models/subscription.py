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
    def create(cls, psid, target, filter_arg, type_arg):

        if target not in cls.Target:
            raise ValueError(f'invalid target: {target}')

        if type_arg not in cls.Type:
            raise ValueError(f'invalid type: {type_arg}')

        if not isinstance(filter_arg, dict):
            raise ValueError(f'filter should be dict: {filter_arg}')

        data = {
            'psid': psid,
            'target': target.value,
            'filter': filter_arg,
            'type': type_arg.value,
        }

        cls.collection.replace_one(data, data, upsert=True)

