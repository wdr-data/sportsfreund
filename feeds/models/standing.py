import locale

from lib.mongodb import db
from .. import api
from .model import FeedModel


locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


class Standing(FeedModel):
    collection = db.standing
    api_function = api.standing
    api_id_name = 'se'

    season_feeds = {'Curling': [24752, 24753, 24754],
                    'Eishockey': [24732, 24733]}

    id = str(id)
    @classmethod
    def transform(cls, standing):
        for round in standing:
            standing = round
            standing['season'] = id
        return standing

    @classmethod
    def load_standings(cls, round=sport):
        if sport is not None:
            for ids in season_feeds[sport]:
                cls.load_feed(id)
        else:
            for sport in season_feeds.items:
                for ids in season_feeds[sport]:
                    cls.load_feed(id)

