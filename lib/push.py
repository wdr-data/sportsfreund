from datetime import datetime
from enum import Enum

from lib.model import Model
from lib.mongodb import db


class Push(Model):
    """
    Record of past pushes
    """

    collection = db.pushes

    class State(Enum):
        SENDING = 'sending'
        SENT = 'sent'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.state not in Push.State:
            self.state = Push.State(self.state)

    @classmethod
    def create(cls, target: dict, state: State, date: datetime):
        """
        Create instance of push in database
        :param target:
        :param state:
        :param date:
        :return:
        """

        if not isinstance(target, dict):
            raise ValueError(f'invalid target: {target}')

        if state not in cls.State:
            raise ValueError(f'invalid state: {state}')

        if not isinstance(date, datetime):
            raise ValueError(f'invalid date: {date}')

        data = {
            'target': target,
            'state': state.value,
            'date': date
        }

        cls.collection.replace_one(data, data, upsert=True)

    @classmethod
    def replace(cls, target: dict, state: State, date: datetime=None):
        """
        Updating state of existing database entry

        :param target:
        :param state:
        :param date:
        :return:
        """

        if not isinstance(target, dict):
            raise ValueError(f'invalid target: {target}')

        if state is not cls.State:
            raise ValueError(f'invalid state: {state}')

        if not isinstance(date, datetime):
            raise ValueError(f'invalid date: {date}')

        data = {
            'state': state.value,
        }

        if date is not None:
            data['date'] = date

        cls.collection.replace_one({'target': target}, data)
