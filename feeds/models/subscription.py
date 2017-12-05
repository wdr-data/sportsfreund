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

    class Type(Enum):
        RESULT = 'result'

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        if self.target not in Subscription.Target:
            for t in Subscription.Target:
                if self.target == t.value:
                    self.target = t
                    break
            else:
                raise ValueError(f'invalid target: {self.target}')

        if self.type not in Subscription.Type:
            for t in Subscription.Type:
                if self.type == t.value:
                    self.type = t
                    break
            else:
                raise ValueError(f'invalid type: {self.type}')

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

    def delete(self) -> None:
        """
        Delete subscription entry from database

        :return:
        """

        Subscription.collection.delete_one({'_id': self._id})
