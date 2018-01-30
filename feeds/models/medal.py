from datetime import datetime
from enum import Enum
from time import time as time

from feeds.config import DISCIPLINE_ALIASES, sport_by_name
from lib.mongodb import db
from .model import ListFeedModel
from .. import api


class Medal(ListFeedModel):
    collection = db.matches_meta
    api_id_name = 'to'

    class Event(Enum):
        OLYMPIA_18 = 'owg18'

    @classmethod
    def api_function(cls, **kwargs):
        kwargs[]
        return api.medals(**kwargs)


    def __init__(self, *args, **kwargs):
        """
        Match metadata model. Do not create instances using this constructor, only use the
        provided factory methods.

        @DynamicAttrs
        """
        super().__init__(*args, **kwargs)

    @property
    def gender_name(self):
        return 'Herren' if self.gender == 'male' else \
            ('Damen' if self.gender == 'female' else 'Mixed')

    @classmethod
    def by_id(cls, id, clear_cache=False):
        raise NotImplementedError

    @classmethod
    def by_match_id(cls, match_id):
        try:
            return cls.query(id=match_id)[0]
        except IndexError:
            return None
