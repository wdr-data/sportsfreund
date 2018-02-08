import locale

from lib.mongodb import db
from .. import api
from .model import FeedModel


locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')


class Standing(FeedModel):
    collection = db.standings
    api_function = api.standing
    api_id_name = 'se'
    cache_time = 60*5

    season_feeds = [24752, 24753, 24754, 24732, 24733]

    id = str(id)

    @classmethod
    def by_season_round(cls, season_id, round_name):
        export = []
        season = cls.query(instance_id=season_id)[0]
        for obj in season['standing']:
            if obj['round']['name'] == round_name:
                export.append(obj)

        return export

    @classmethod
    def transform(cls, standing):
        round = standing['standing']
        standing['standing'] = round

        return standing

    @classmethod
    def load_standings(cls):
        for id in cls.season_feeds:
            cls.by_id(id)

