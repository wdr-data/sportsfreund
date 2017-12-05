from lib.mongodb import db
from .model import Model
from enum import Enum


class Subscription(Model):
    """
    Each subscription instance describes a tuple of user, target, filter, type
    user describes who subscribed
    target describes what kind of entity triggers the subscription
    filter describes which attributes the target entity must have
    type describes which kind of event triggers the subscription
    """

    collection = db.subscriptions

    class Target(Enum):
        SPORT = 'sport'
        DISCIPLINE = 'discipline'
        ATHLETE = 'athlete'
        HIGHLIGHT = 'highlight'

    class Type(Enum):
        RESULT = 'result'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.target not in Subscription.Target:
            self.target = Subscription.Target(self.target)

        if self.type not in Subscription.Type:
            self.type = Subscription.Type(self.type)

    @classmethod
    def create(cls, psid: str, target: Target, filter_arg: dict, type_arg: Type) -> None:
        """
        Create subscription entry in database

        :param psid: user ID
        :param target:
        :param filter_arg:
        :param type_arg:
        :return:
        """

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

    @staticmethod
    def describe_filter(filter_arg):
        if 'sport' in filter_arg and not 'discipline' in filter_arg:
            return filter_arg['sport']
        if 'discipline' in filter_arg:
            return f"{filter_arg['sport']}/{filter_arg['discipline']}"
        if 'athlete' in filter_arg:
            return filter_arg['athlete']
